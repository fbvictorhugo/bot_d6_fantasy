from d6_bot.bot import get_discord_token, main


if __name__ == "__main__":
    try:
        get_discord_token()
        print("Starting D6 Fantasy bot...")
    except Exception as exc:
        print(f"Failed to start bot: {exc}")
        raise
    main()
