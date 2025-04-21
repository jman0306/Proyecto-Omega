import grpc
import turbo_message_pb2
import turbo_message_pb2_grpc

def menu():
    print("\n--- TurboMessage ---")
    print("1. Registrarse")
    print("2. Iniciar sesión")
    print("3. Salir")
    return input("Elige una opción: ")

def user_menu():
    print("\n--- Menú del Usuario ---")
    print("1. Enviar mensaje")
    print("2. Ver bandeja de entrada")
    print("3. Ver bandeja de salida")
    print("4. Leer mensaje")
    print("5. Borrar mensaje")
    print("6. Cerrar sesión")
    return input("Elige una opción: ")

def prompt_credentials():
    username = input("Usuario: ")
    password = input("Contraseña: ")
    return username, password

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = turbo_message_pb2_grpc.TurboMessageStub(channel)
        logged_in = False
        current_user = ""

        while True:
            if not logged_in:
                choice = menu()
                if choice == "1":
                    username, password = prompt_credentials()
                    response = stub.RegisterUser(turbo_message_pb2.UserCredentials(username=username, password=password))
                    print(response.message)
                elif choice == "2":
                    username, password = prompt_credentials()
                    response = stub.Login(turbo_message_pb2.UserCredentials(username=username, password=password))
                    print(response.message)
                    if response.success:
                        logged_in = True
                        current_user = username
                elif choice == "3":
                    print("Saliendo...")
                    break
                else:
                    print("Opción inválida")
            else:
                choice = user_menu()
                if choice == "1":
                    recipient = input("Destinatario: ")
                    subject = input("Asunto: ")
                    body = input("Mensaje: ")
                    response = stub.SendMail(turbo_message_pb2.MailRequest(
                        sender=current_user,
                        recipient=recipient,
                        subject=subject,
                        body=body
                    ))
                    print(response.message)
                elif choice == "2":
                    mails = stub.GetInbox(turbo_message_pb2.User(username=current_user))
                    print("\n--- Bandeja de Entrada ---")
                    for mail in mails.mails:
                        status = "Leído" if mail.read else "No leído"
                        print(f"ID: {mail.id} | De: {mail.sender} | Asunto: {mail.subject} | Estado: {status}")
                elif choice == "3":
                    mails = stub.GetOutbox(turbo_message_pb2.User(username=current_user))
                    print("\n--- Bandeja de Salida ---")
                    for mail in mails.mails:
                        print(f"ID: {mail.id} | Para: {mail.recipient} | Asunto: {mail.subject}")
                elif choice == "4":
                    mail_id = int(input("ID del mensaje a leer: "))
                    mail = stub.ReadMail(turbo_message_pb2.MailId(username=current_user, id=mail_id))
                    print(f"\nDe: {mail.sender}\nPara: {mail.recipient}\nAsunto: {mail.subject}\n\n{mail.body}")
                elif choice == "5":
                    mail_id = int(input("ID del mensaje a borrar: "))
                    response = stub.DeleteMail(turbo_message_pb2.MailId(username=current_user, id=mail_id))
                    print(response.message)
                elif choice == "6":
                    logged_in = False
                    current_user = ""
                    print("Sesión cerrada.")
                else:
                    print("Opción inválida")

if __name__ == '__main__':
    run()
