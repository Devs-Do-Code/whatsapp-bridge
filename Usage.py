from shubh_whatsapp import WhatsappClient, WhatsappPkgError, BridgeError
import time
import os

# --- Basic Initialization ---
# This will automatically check prerequisites, clone the repo if needed,
# and start the Go bridge. It will block until connected or QR scan needed.
try:
    print("Initializing WhatsApp Client...")
    # The data directory will default to ~/.my_whatsapp_pkg_data or %APPDATA%/MyWhatsappPkg
    client = WhatsappClient(auto_setup=True, auto_connect=True)
    print("Client initialized and bridge connected.")

except (WhatsappPkgError, BridgeError) as e:
    print(f"Failed to initialize client: {e}")
    exit()
except KeyboardInterrupt:
     print("Initialization interrupted.")
     # Optional: try to clean up if bridge started
     # client.disconnect() # Need to handle client not fully initialized
     exit()


# --- Sending Messages ---
try:
    # Replace with a real number or JID
    recipient_jid = "919575855770@s.whatsapp.net" # Use JID for reliability if known
    print(f"\nSending text message to {recipient_jid}...")
    if client.send_message(recipient_jid, "Hello from my Python Package! 👋"):
        print("Text message sent successfully.")
    else:
        print("Failed to send text message.")

    # Replace with a real file path
    # media_path = "/path/to/your/image.jpg"
    # if os.path.exists(media_path):
    #    print(f"\nSending media file {media_path}...")
    #    if client.send_media(recipient_jid, media_path, caption="Check out this file!"):
    #        print("Media sent successfully.")
    #    else:
    #        print("Failed to send media.")
    # else:
    #    print(f"Media file not found: {media_path}")

except BridgeError as e:
    print(f"Bridge Error: {e}. Cannot perform action.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")


# --- Receiving New Messages (Polling) ---
print("\nStarting message polling loop (press Ctrl+C to stop)...")
try:
    while True:
        if not client._bridge_manager.check_if_alive():
             print("Bridge process died. Exiting loop.")
             break

        print(f"\n[{time.strftime('%H:%M:%S')}] Checking for new messages...")
        new_messages = client.get_new_messages(download_media=True) # Auto-download media

        if new_messages:
            print(f"--- Received {len(new_messages)} New Message(s) ---")
            for msg in new_messages:
                 # Display timestamp in local time
                 local_timestamp_str = msg['timestamp'].astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
                 sender = msg['sender']
                 content = msg['content']
                 media_info = ""
                 if msg['media_type']:
                      media_info = f" [{msg['media_type']}: {msg.get('filename', 'N/A')}]"
                      local_path = msg.get('local_media_path')
                      if local_path:
                           if "FAILED" in local_path or "ERROR" in local_path:
                                media_info += f" (Download Status: {local_path})"
                           else:
                                media_info += f" (Downloaded: {os.path.basename(local_path)})"
                      else:
                           media_info += " (Download Pending/Not Attempted)"


                 # Print only incoming messages
                 if not msg['is_from_me']:
                      print(f"[{local_timestamp_str}] From: {sender} in Chat: {msg['chat_jid']}")
                      print(f"  Content: '{content}'{media_info}")
                      print("-" * 10)
            print("------------------------------------")
        else:
            print("No new messages found.")

        # Wait before next check
        wait_time = 30 # Check every 30 seconds
        print(f"Waiting {wait_time} seconds...")
        time.sleep(wait_time)

except KeyboardInterrupt:
    print("\nStopping message polling.")
except BridgeError as e:
     print(f"\nBridge Error during polling: {e}")
finally:
    # --- Clean Shutdown ---
    print("Disconnecting bridge...")
    client.disconnect()
    print("Client disconnected.")