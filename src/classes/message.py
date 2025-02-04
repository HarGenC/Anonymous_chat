class User:
    id:int

    def __init__(self, id) -> None:
        self.id = id

class Message:
    text:str
    from_user:User
    id:int
    file_id:str

    def __init__(self, text:str, id:int, msg_id:int, file_id:str = "None") -> None:
        self.text = text
        self.from_user = User(id)
        self.id = msg_id
        self.file_id = file_id