import sys
import time
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO,format="%(asctime)s - %(levelname)s - %(message)s",datefmt="%Y-%m-%d %H:%M:%S",)
log=logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL=1
BASE_DATA_DIR=Path("Data")

try:
    src_path=str(Path(__file__).resolve().parent.parent/"src")
    sys.path.insert(0,src_path)
except Exception as e:
    log.error(f"Error adjusting sys.path: {e}.",exc_info=True)
    sys.exit(1)
try:
    from whatsapp_bridge import WhatsappClient,WhatsappPkgError,BridgeError,__version__
except ImportError as e:
    log.critical(f"Failed to import whatsapp_bridge: {e}",exc_info=True)
    sys.exit(1)

class MessageListener:

    def __init__(self,poll_interval:int=DEFAULT_POLL_INTERVAL):
        self.client=None
        self.poll_interval=poll_interval
        self._running=False
    
    def _initialize_client(self)->bool:
        try:
            self.client=WhatsappClient(auto_setup=True,auto_connect=True)
            return True
        except (WhatsappPkgError,BridgeError) as e:
            log.error(f"Failed to initialize client or connect bridge: {e}",exc_info=True)
            return False
        except Exception as e:
            log.error(f"Unexpected error: {e}",exc_info=True)
            return False
    
    def _process_message(self,message:Dict[str,Any]):
        try:
            local_timestamp=message.get("timestamp")
            local_timestamp_str=local_timestamp.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z") if isinstance(local_timestamp,datetime) else "N/A"
            sender_jid=message.get("sender","Unknown_Sender")
            chat_jid=message.get("chat_jid","Unknown_Chat")
            contact_name=sender_jid
            try:
                if self.client and hasattr(self.client,"get_contact_info"):
                    contact_info=self.client.get_contact_info(sender_jid)
                    if contact_info and contact_info.get("name"):
                        contact_name=contact_info["name"]
                elif message.get("sender_name"):
                    contact_name=message.get("sender_name")
            except Exception:
                pass
            content=message.get("content","")
            media_type=message.get("media_type")
            original_media_path_str=message.get("local_media_path")
            media_filename=message.get("filename")
            media_log_info="No media attached."
            if media_type and original_media_path_str and media_filename:
                original_media_path=Path(original_media_path_str)
                media_log_info=f"Media Type: {media_type}, Filename: {media_filename}"
                if "FAILED" not in original_media_path_str.upper() and "ERROR" not in original_media_path_str.upper() and original_media_path.is_file():
                    target_chat_dir=BASE_DATA_DIR/chat_jid
                    try:
                        target_chat_dir.mkdir(parents=True,exist_ok=True)
                    except OSError:
                        media_log_info+=" (Error creating target directory)"
                    else:
                        new_media_path=target_chat_dir/media_filename
                        try:
                            shutil.move(str(original_media_path),str(new_media_path))
                            media_log_info+=f" (Moved to: {new_media_path})"
                        except FileNotFoundError:
                            media_log_info+=" (Original file not found for move)"
                        except Exception:
                            media_log_info+=" (Error moving file)"
                else:
                    media_log_info+=f" (Download Status: {original_media_path_str})"
            log.info(f"{local_timestamp_str} {chat_jid} {contact_name} {sender_jid} '{content}' {media_log_info}")
        except Exception as e:
            log.error(f"Error processing message: {e}",exc_info=True)
    
    def listen(self):
        try:
            BASE_DATA_DIR.mkdir(parents=True,exist_ok=True)
        except OSError:
            return
        if not self._initialize_client():
            return
        self._running=True
        try:
            while self._running:
                try:
                    if self.client and hasattr(self.client,'_bridge_manager') and self.client._bridge_manager.check_if_alive():
                        new_messages=self.client.get_new_messages(download_media=True)
                        if new_messages:
                            for message in new_messages:
                                self._process_message(message)
                    else:
                        self._running=False
                        break
                    time.sleep(self.poll_interval)
                except BridgeError:
                    time.sleep(self.poll_interval)
                except Exception:
                    time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            self._running=False
        finally:
            self._cleanup()
    
    def stop(self):
        self._running=False
    
    def _cleanup(self):
        if self.client and hasattr(self.client,"disconnect"):
            try:
                self.client.disconnect()
            except Exception:
                pass

if __name__=="__main__":
    listener=MessageListener()
    listener.listen()
