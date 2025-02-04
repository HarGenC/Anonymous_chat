import json
import logging

class OutputManager():
    _history:list

    def __init__(self, history:list) -> None:
        self._history = history
    
    async def do_json_format_output(self) -> json:
        logging.info("Преобразование истории в json формат")
        result = {"message":[]}
        
        counter = 0
        for msg in self._history:
            message_text = ""
            file_text = ""
            if not msg[3] == "None":
                counter += 1
                file_text = f"file_{counter}\n"
            if not msg[4] == "None":
                message_text = str(msg[4])
            message = {
                "id:username": f"{msg[1]}:{msg[7]}",
                "file": file_text,
                "text": message_text
            }
            result["message"].append(message)
        return result
    
    async def do_for_chatgpt_output(self, chatgpt_id:int) -> list:
        logging.info("Преобразование истории под формат чатГПТ")
        result = []
        
        for msg in self._history:
            message_text = msg[4]
            role = "user"
            if msg[1] == chatgpt_id:
                role = "assistant" 

            result.append({'role': role, 'content': message_text})
        return result