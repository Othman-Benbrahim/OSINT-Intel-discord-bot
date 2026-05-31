"""
Bot Discord OSINT-Intel — version HuggingFace Inference Providers
Utilise le nouveau routeur HuggingFace (router.huggingface.co) + DuckDuckGo.
"""

import os
import asyncio
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

from osint_skill import OSINT_SYSTEM_PROMPT, FORMATS, DEFAULT_FORMAT
from web_search import search_web, should_search

# ── Configuration ─────────────────────────────────────────────────────────────
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
HF_TOKEN      = os.getenv("HF_TOKEN")
HF_MODEL      = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
MAX_TOKENS    = 8192
DISCORD_MAX   = 1900

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("osint-bot")

# ── Sessions par utilisateur ──────────────────────────────────────────────────
user_sessions: dict[int, list[dict]] = {}
MAX_HISTORY = 10

# ── Client HuggingFace via routeur OpenAI-compatible ─────────────────────────
hf_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def split_message(text: str, limit: int = DISCORD_MAX) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


def build_messages(user_id: int, user_content: str, mode: str = "OSINT") -> list[dict]:
    history = user_sessions.get(user_id, [])
    format_instructions = FORMATS.get(mode, DEFAULT_FORMAT)
    full_user_content = f"{format_instructions}\n\n---\nREQUÊTE : {user_content}"
    return (
        [{"role": "system", "content": OSINT_SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": full_user_content}]
    )


def save_turn(user_id: int, user_msg: str, assistant_msg: str):
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    user_sessions[user_id].append({"role": "user",      "content": user_msg})
    user_sessions[user_id].append({"role": "assistant", "content": assistant_msg})
    if len(user_sessions[user_id]) > MAX_HISTORY * 2:
        user_sessions[user_id] = user_sessions[user_id][-(MAX_HISTORY * 2):]


async def call_hf(user_id: int, query: str, mode: str = "OSINT") -> str:
    # ── Recherche web conditionnelle ──────────────────────────────────────────
    enriched_query = query
    if should_search(query):
        log.info("Recherche web activée...")
        web_ctx = await asyncio.get_event_loop().run_in_executor(
            None, search_web, query
        )
        enriched_query = (
            f"{web_ctx}\n\n---\n"
            f"En tenant compte de ces résultats récents, réponds à la requête suivante "
            f"en citant obligatoirement tes sources avec le format [N] dans le texte, "
            f"et en listant toutes les sources utilisées à la fin sous "
            f"📚 SOURCES (format : [N] Titre — URL) :\n\n{query}"
        )

    messages = build_messages(user_id, enriched_query, mode)

    def _sync_call():
        response = hf_client.chat.completions.create(
            model=HF_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=0.4,
        )
        return response.choices[0].message.content

    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _sync_call)
    except Exception as e:
        raise RuntimeError(f"Erreur HuggingFace : {e}") from e

    save_turn(user_id, query, result)
    return result


# ── Bot Discord ───────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    await tree.sync()
    log.info(f"✅ Bot connecté : {bot.user} (ID: {bot.user.id})")
    log.info(f"📡 Modèle : {HF_MODEL}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="les signaux faibles 🔍"
        )
    )


@tree.command(name="osint", description="Analyse OSINT / Renseignement stratégique avec recherche web")
@app_commands.describe(
    requete="Votre question ou sujet d'analyse",
    mode="Mode d'analyse (optionnel)"
)
@app_commands.choices(mode=[
    app_commands.Choice(name="🔎 OSINT – Analyse terrain complète", value="OSINT"),
    app_commands.Choice(name="⚡ EXPRESS – Synthèse rapide 4 blocs",  value="EXPRESS"),
    app_commands.Choice(name="📈 FORECAST – Prédiction probabilisée", value="FORECAST"),
    app_commands.Choice(name="🔄 UPDATE – Mise à jour bayésienne",     value="UPDATE"),
    app_commands.Choice(name="📊 CALIBRATION – Scoring prédictions",  value="CALIBRATION"),
])
async def osint_command(
    interaction: discord.Interaction,
    requete: str,
    mode: Optional[app_commands.Choice[str]] = None,
):
    await interaction.response.defer(thinking=True)
    mode_prefix = f"[Mode : {mode.value}]\n\n" if mode else ""
    full_query  = f"{mode_prefix}{requete}"
    log.info(f"[{interaction.user}] /osint → {requete[:80]}...")

    mode_key = mode.value if mode else "OSINT"

    try:
        result = await call_hf(interaction.user.id, requete, mode_key)
    except RuntimeError as e:
        await interaction.followup.send(f"❌ {e}")
        return
    except Exception as e:
        log.exception("Erreur inattendue")
        await interaction.followup.send(f"❌ Erreur inattendue : `{e}`")
        return

    # Crée un thread à partir du message de réponse initial
    thread_name = requete[:50] + ("..." if len(requete) > 50 else "")
    chunks = split_message(result)
    log.info(f"Envoi de {len(chunks)} message(s) dans le thread")

    try:
        # 1. Accuser réception via followup (efface le "réfléchit...")
        await interaction.followup.send("✅ Analyse prête.", ephemeral=True)

        # 2. Poster un message normal dans le salon (support de thread fiable)
        anchor = await interaction.channel.send(f"**{thread_name}**")

        # 3. Créer le thread depuis ce message
        thread = await anchor.create_thread(
            name=thread_name,
            auto_archive_duration=1440
        )

        # 4. Envoyer les chunks dans le thread
        for i, chunk in enumerate(chunks):
            await thread.send(chunk)
            if i < len(chunks) - 1:
                await asyncio.sleep(0.8)

    except discord.Forbidden:
        log.warning("Permission refusée — fallback salon")
        await interaction.followup.send(chunks[0])
        for chunk in chunks[1:]:
            await asyncio.sleep(0.8)
            await interaction.channel.send(chunk)
    except Exception as e:
        log.error(f"Erreur thread : {e}")
        await interaction.followup.send(chunks[0])
        for chunk in chunks[1:]:
            await asyncio.sleep(0.8)
            await interaction.channel.send(chunk)


@tree.command(name="reset_session", description="Réinitialise votre historique de conversation OSINT")
async def reset_session(interaction: discord.Interaction):
    user_sessions.pop(interaction.user.id, None)
    await interaction.response.send_message("🔄 Session réinitialisée.", ephemeral=True)


@tree.command(name="osint_help", description="Aide et exemples d'utilisation du bot OSINT-Intel")
async def osint_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔍 OSINT-Intel Bot — Guide d'utilisation",
        description=(
            f"Analyste IA en renseignement stratégique.\n"
            f"**Modèle :** `{HF_MODEL}`\n"
            f"**Recherche web :** DuckDuckGo (automatique)"
        ),
        color=0x2F3136
    )
    embed.add_field(
        name="📌 Commandes",
        value=(
            "`/osint [requête] [mode]` — Analyse principale\n"
            "`/reset_session` — Effacer l'historique\n"
            "`/osint_help` — Ce message"
        ),
        inline=False
    )
    embed.add_field(
        name="🎯 Modes",
        value=(
            "**OSINT** — Analyse terrain complète (11 étapes)\n"
            "**EXPRESS** — Synthèse rapide (4 blocs)\n"
            "**FORECAST** — Prédiction probabilisée\n"
            "**UPDATE** — Mise à jour bayésienne\n"
            "**CALIBRATION** — Scoring de prédictions"
        ),
        inline=False
    )
    embed.add_field(
        name="💡 Exemples",
        value=(
            "`/osint Signaux faibles autour de la politique énergétique française`\n"
            "`/osint Profil stratégique de SpaceX` mode:OSINT\n"
            "`/osint Probabilité récession zone euro 12 mois` mode:FORECAST"
        ),
        inline=False
    )
    embed.set_footer(text="Sources ouvertes — Garde-fous éthiques actifs")
    await interaction.response.send_message(embed=embed)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if bot.user in message.mentions:
        query = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not query:
            await message.reply("Mentionnez-moi avec une question, ou utilisez `/osint`.")
            return
        async with message.channel.typing():
            try:
                result = await call_hf(message.author.id, query, "OSINT")
            except Exception as e:
                await message.reply(f"❌ Erreur : `{e}`")
                return
        for i, chunk in enumerate(split_message(result)):
            if i == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(chunk)
    await bot.process_commands(message)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN manquant dans .env")
    if not HF_TOKEN:
        raise ValueError("❌ HF_TOKEN manquant dans .env")
    log.info(f"Démarrage avec le modèle : {HF_MODEL}")
    bot.run(DISCORD_TOKEN, log_handler=None)
