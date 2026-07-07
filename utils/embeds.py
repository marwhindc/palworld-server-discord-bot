import discord
from datetime import datetime
from typing import Optional, List, Dict, Any

class EmbedColor:
    SUCCESS = 0x2ecc71      # Green
    IN_PROGRESS = 0xf1c40f  # Yellow
    ERROR = 0xe74c3c        # Red

def create_embed(
    title: str,
    description: Optional[str] = None,
    color: int = EmbedColor.SUCCESS,
    fields: Optional[List[Dict[str, Any]]] = None,
    thumbnail_url: Optional[str] = None,
    footer_text: Optional[str] = "Palworld Server Manager"
) -> discord.Embed:
    """Creates a basic Discord Embed with a timestamp, title, description, and optional fields."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", True)
            )
            
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
        
    if footer_text:
        embed.set_footer(text=footer_text)
        
    return embed

def success_embed(title: str, description: Optional[str] = None, fields: Optional[List[Dict[str, Any]]] = None) -> discord.Embed:
    """Returns a green success embed."""
    return create_embed(
        title=f"🟢 {title}",
        description=description,
        color=EmbedColor.SUCCESS,
        fields=fields
    )

def info_embed(title: str, description: Optional[str] = None, fields: Optional[List[Dict[str, Any]]] = None) -> discord.Embed:
    """Returns a yellow in-progress/info embed."""
    return create_embed(
        title=f"🟡 {title}",
        description=description,
        color=EmbedColor.IN_PROGRESS,
        fields=fields
    )

def error_embed(title: str, description: Optional[str] = None, fields: Optional[List[Dict[str, Any]]] = None) -> discord.Embed:
    """Returns a red error/failure embed."""
    return create_embed(
        title=f"🔴 {title}",
        description=description,
        color=EmbedColor.ERROR,
        fields=fields
    )
