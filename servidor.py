import grpc
from concurrent import futures
import turbo_message_pb2
import turbo_message_pb2_grpc
import json
import os
from threading import Lock

USERS_FILE = "users.json"
MAILS_FILE = "mails.json"
user_lock = Lock()
mail_lock = Lock()

# Inicializar almacenamiento si no existen
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(MAILS_FILE):
    with open(MAILS_FILE, "w") as f:
        json.dump({}, f)

class TurboMessageServicer(turbo_message_pb2_grpc.TurboMessageServicer):
    def load_users(self):
        with open(USERS_FILE, "r") as f:
            return json.load(f)

    def save_users(self, users):
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

    def load_mails(self):
        with open(MAILS_FILE, "r") as f:
            return json.load(f)

    def save_mails(self, mails):
        with open(MAILS_FILE, "w") as f:
            json.dump(mails, f)

    def RegisterUser(self, request, context):
        with user_lock:
            users = self.load_users()
            if request.username in users:
                return turbo_message_pb2.Response(success=False, message="Usuario ya existe.")
            users[request.username] = {"password": request.password}
            self.save_users(users)
            return turbo_message_pb2.Response(success=True, message="Registro exitoso.")

    def Login(self, request, context):
        users = self.load_users()
        if request.username in users and users[request.username]["password"] == request.password:
            return turbo_message_pb2.Response(success=True, message="Inicio de sesión exitoso.")
        return turbo_message_pb2.Response(success=False, message="Credenciales incorrectas.")

    def SendMail(self, request, context):
        with mail_lock:
            mails = self.load_mails()
            users = self.load_users()
            if request.recipient not in users:
                return turbo_message_pb2.Response(success=False, message="Receptor no existe.")

            inbox = [m for m in mails.values() if m["recipient"] == request.recipient]
            if len(inbox) >= 5:
                return turbo_message_pb2.Response(success=False, message="Bandeja de entrada del receptor llena.")

            outbox = [m for m in mails.values() if m["sender"] == request.sender]
            if len(outbox) >= 5:
                return turbo_message_pb2.Response(success=False, message="Tu bandeja de salida está llena.")

            mail_id = str(max([int(k) for k in mails.keys()] + [0]) + 1)
            mails[mail_id] = {
                "id": int(mail_id),
                "subject": request.subject,
                "sender": request.sender,
                "recipient": request.recipient,
                "body": request.body,
                "read": False
            }
            self.save_mails(mails)
            return turbo_message_pb2.Response(success=True, message="Correo enviado.")

    def GetInbox(self, request, context):
        mails = self.load_mails()
        inbox = [m for m in mails.values() if m["recipient"] == request.username]
        return turbo_message_pb2.MailList(mails=[
            turbo_message_pb2.Mail(**m) for m in inbox
        ])

    def GetOutbox(self, request, context):
        mails = self.load_mails()
        outbox = [m for m in mails.values() if m["sender"] == request.username]
        return turbo_message_pb2.MailList(mails=[
            turbo_message_pb2.Mail(**m) for m in outbox
        ])

    def ReadMail(self, request, context):
        with mail_lock:
            mails = self.load_mails()
            mail = mails.get(str(request.id))
            if not mail or (mail["sender"] != request.username and mail["recipient"] != request.username):
                context.abort(grpc.StatusCode.NOT_FOUND, "Correo no encontrado.")
            if mail["recipient"] == request.username and not mail["read"]:
                mail["read"] = True
                self.save_mails(mails)
            return turbo_message_pb2.Mail(**mail)

    def DeleteMail(self, request, context):
        with mail_lock:
            mails = self.load_mails()
            mail = mails.get(str(request.id))
            if not mail or (mail["sender"] != request.username and mail["recipient"] != request.username):
                return turbo_message_pb2.Response(success=False, message="Correo no encontrado.")
            del mails[str(request.id)]
            self.save_mails(mails)
            return turbo_message_pb2.Response(success=True, message="Correo borrado.")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    turbo_message_pb2_grpc.add_TurboMessageServicer_to_server(TurboMessageServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Servidor TurboMessage corriendo en el puerto 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
