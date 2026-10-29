import os
import pprint


def log_debug_data(data_label: str, data_content, type: str = "info"):

    backend_root_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    logs_dir = os.path.join(backend_root_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    if type == "error":
        filename = "debug_error_log.txt"
    elif type == "chat_faq":
        filename = "debug_chat_faq_log.txt"
    else:
        filename = "debug_chat_log.txt"

    log_path = os.path.join(logs_dir, filename)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n" + "="*50 + "\n")
        f.write(f"TIMESTAMP / LABEL: {data_label}\n")
        f.write("-" * 50 + "\n")
        if isinstance(data_content, (dict, list)):
            f.write(pprint.pformat(data_content, indent=4, width=80))
        else:
            f.write(str(data_content))
        f.write("\n" + "="*50 + "\n")