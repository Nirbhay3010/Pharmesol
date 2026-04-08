import sys
from dotenv import load_dotenv
from pharmacy_lookup import lookup_by_phone
from prompts import build_system_prompt
from agent import SalesAgent

DEFAULT_PHONE = "+1-555-123-4567"  # HealthFirst Pharmacy
EXIT_PHRASES = {"bye", "end call", "hang up", "goodbye", "exit", "quit"}


def main():
    load_dotenv()

    print("=" * 60)
    print("  Pharmesol Inbound Sales Agent — Text Simulation")
    print("=" * 60)
    print()

    # Step 1: Get caller phone number
    phone = input(
        f"Enter caller phone number (or press Enter for default {DEFAULT_PHONE}): "
    ).strip()
    if not phone:
        phone = DEFAULT_PHONE

    # Step 2: Look up pharmacy by phone (fires before greeting, per design doc)
    print(f"\n[SYSTEM] Looking up caller: {phone} ...")
    pharmacy = lookup_by_phone(phone)

    if pharmacy:
        print(f"[SYSTEM] Identified: {pharmacy['name']} — {pharmacy['city']}, {pharmacy['state']}")
        print(f"[SYSTEM] Rx volume: ~{pharmacy['rx_volume']} prescriptions/month")
    else:
        print("[SYSTEM] Pharmacy not found in database — new lead.")

    # Step 3: Build system prompt and initialize agent
    system_prompt = build_system_prompt(pharmacy)
    agent = SalesAgent(system_prompt)

    # Step 4: Generate and display the opening greeting
    print("\n" + "-" * 60)
    greeting = agent.generate_greeting()
    print(f"\nAgent: {greeting}\n")

    # Step 5: Conversation loop
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n[SYSTEM] Call ended.")
            break

        if not user_input:
            continue

        if user_input.lower() in EXIT_PHRASES:
            # Let the agent say goodbye naturally
            farewell = agent.chat(user_input)
            print(f"\nAgent: {farewell}\n")
            print("[SYSTEM] Call ended.")
            break

        response = agent.chat(user_input)
        print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    main()
