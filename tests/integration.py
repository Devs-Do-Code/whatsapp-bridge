import sys
import os
import time
from pathlib import Path

try:
    project_root=Path(__file__).resolve().parent.parent
    src_path=project_root/"src"
    if str(src_path) not in sys.path:
        sys.path.insert(0,str(src_path))
except Exception as e:
    print(f"Error adjusting sys.path: {e}.",file=sys.stderr)
    sys.exit(1)

try:
    from whatsapp_bridge import WhatsappClient,WhatsappPkgError,BridgeError,__version__
except ImportError as e:
    print(f"Failed to import whatsapp_bridge: {e}",file=sys.stderr)
    sys.exit(1)

def run_test():
    client=None
    print("\n>>> Initializing WhatsApp Bridge Client for Test...")
    try:
        client=WhatsappClient(auto_setup=True,auto_connect=True)
        print("Client initialized and bridge connected successfully.")
    except (WhatsappPkgError,BridgeError) as e:
        print(f"TEST FAILED: Failed to initialize client: {e}",file=sys.stderr)
        return
    except KeyboardInterrupt:
        if client and hasattr(client,"disconnect"):
            client.disconnect()
        return
    print(f"\n>>> Sending Test Message...")
    try:
        test_recipient=os.getenv("WHATSAPP_TEST_RECIPIENT","1234567890@s.whatsapp.net")
        print(f"   Recipient: {test_recipient}")
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        test_message=f"Automated test message from whatsapp_bridge v{__version__} at {timestamp}"
        if client.send_message(test_recipient,test_message):
            print("Test message sent successfully (API success).")
        else:
            print("TEST FAILED: Failed to send test message (API failure).",file=sys.stderr)
    except BridgeError as e:
        print(f"TEST FAILED: Bridge Error during sending: {e}.",file=sys.stderr)
    except Exception as e:
        print(f"TEST FAILED: Unexpected error during sending: {e}",file=sys.stderr)
    print("\n>>> Checking for New Messages (Short Poll)...")
    try:
        for i in range(2):
            print(f"\n[{time.strftime('%H:%M:%S')}] Polling attempt {i+1}...")
            if not client._bridge_manager.check_if_alive():
                print("TEST FAILED: Bridge process died unexpectedly.",file=sys.stderr)
                break
            new_messages=client.get_new_messages(download_media=True)
            if new_messages:
                print(f"   Received {len(new_messages)} New Message(s):")
                for msg in new_messages:
                    local_timestamp_str=msg["timestamp"].astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
                    sender=msg.get("sender","Unknown")
                    content=msg.get("content","")
                    media_info=""
                    if msg.get("media_type"):
                        media_info=f" [{msg['media_type']}: {msg.get('filename','N/A')}]"
                        local_path=msg.get("local_media_path")
                        if local_path:
                            if "FAILED" in local_path or "ERROR" in local_path:
                                media_info+=f" (Download Status: {local_path})"
                            else:
                                media_info+=f" (Downloaded: {os.path.basename(local_path)})"
                    print(f"     [{local_timestamp_str}] From: {sender} Chat: {msg.get('chat_jid','Unknown')}")
                    print(f"       Content: '{content}'{media_info}")
            else:
                print("   No new messages found during this poll.")
            if i<1:
                wait_time=5
                print(f"Waiting {wait_time} seconds before next poll...")
                time.sleep(wait_time)
    except KeyboardInterrupt:
        pass
    except BridgeError as e:
        print(f"\nTEST FAILED: Bridge Error during polling: {e}",file=sys.stderr)
    except Exception as e:
        print(f"\nTEST FAILED: Unexpected error during polling: {e}",file=sys.stderr)
    finally:
        print("\n>>> Test Finished: Disconnecting Bridge...")
        if client and hasattr(client,"disconnect"):
            client.disconnect()
        else:
            print("Client object not available for disconnect.")
            
if __name__=="__main__":
    run_test()
