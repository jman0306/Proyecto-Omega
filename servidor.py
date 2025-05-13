import grpc
from concurrent import futures
import turbo_message_pb2
import turbo_message_pb2_grpc
import json
import os
from threading import Lock

USERS_FILE = "users.json"
MAILS_FILE = "mails.json"
user_mail_lock = Lock()  # Lock único para evitar condiciones de carrera

# Inicializar archivos si no existen
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
        with user_mail_lock:
            users = self.load_users()
            if request.username in users:
                return turbo_message_pb2.Response(success=False, message="Usuario ya existe.")
            users[request.username] = {"password": request.password}
            self.save_users(users)

            mails = self.load_mails()
            mails[request.username] = {"inbox": {}, "sent": {}}
            self.save_mails(mails)

            return turbo_message_pb2.Response(success=True, message="Registro exitoso.")

    def Login(self, request, context):
        with user_mail_lock:
            users = self.load_users()
            if request.username in users and users[request.username]["password"] == request.password:
                return turbo_message_pb2.Response(success=True, message="Inicio de sesión exitoso.")
            return turbo_message_pb2.Response(success=False, message="Credenciales incorrectas.")

    def SendMail(self, request, context):
        with user_mail_lock:
            mails = self.load_mails()
            users = self.load_users()
            if request.recipient not in users:
                return turbo_message_pb2.Response(success=False, message="Receptor no existe.")

            inbox = mails.get(request.recipient, {}).get("inbox", {})
            if len(inbox) >= 5:
                return turbo_message_pb2.Response(success=False, message="Bandeja de entrada del receptor llena.")

            outbox = mails.get(request.sender, {}).get("sent", {})
            if len(outbox) >= 5:
                return turbo_message_pb2.Response(success=False, message="Tu bandeja de salida está llena.")

            # Calcular nuevo ID
            mail_id = str(max([int(k) for user in mails.values() for folder in user.values() for k in folder.keys()] + [0]) + 1)

            new_mail = {
                "id": int(mail_id),
                "subject": request.subject,
                "sender": request.sender,
                "recipient": request.recipient,
                "body": request.body,
                "read": False
            }

            mails[request.sender]["sent"][mail_id] = new_mail
            mails[request.recipient]["inbox"][mail_id] = new_mail.copy()
            self.save_mails(mails)

            return turbo_message_pb2.Response(success=True, message="Correo enviado.")

    def GetInbox(self, request, context):
        with user_mail_lock:
            mails = self.load_mails()
            inbox = mails.get(request.username, {}).get("inbox", {})
            return turbo_message_pb2.MailList(mails=[
                turbo_message_pb2.Mail(**m) for m in inbox.values()
            ])

    def GetOutbox(self, request, context):
        with user_mail_lock:
            mails = self.load_mails()
            outbox = mails.get(request.username, {}).get("sent", {})
            return turbo_message_pb2.MailList(mails=[
                turbo_message_pb2.Mail(**m) for m in outbox.values()
            ])

    def ReadMail(self, request, context):
        with user_mail_lock:
            mails = self.load_mails()
            user_mails = mails.get(request.username, {}).get("inbox", {})
            mail = user_mails.get(str(request.id))
            if not mail:
                context.abort(grpc.StatusCode.NOT_FOUND, "Correo no encontrado.")
            if not mail["read"]:
                mail["read"] = True
                self.save_mails(mails)
            return turbo_message_pb2.Mail(**mail)

    def DeleteMail(self, request, context):
        with user_mail_lock:
            mails = self.load_mails()
            user_data = mails.get(request.username, {})
            if str(request.id) in user_data.get("inbox", {}):
                del user_data["inbox"][str(request.id)]
            elif str(request.id) in user_data.get("sent", {}):
                del user_data["sent"][str(request.id)]
            else:
                return turbo_message_pb2.Response(success=False, message="Correo no encontrado.")
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
