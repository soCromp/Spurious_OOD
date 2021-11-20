import smtplib, ssl

port = 465  # For SSL
password = 'a5SKs5KBL@K53BPm' # THIS IS A THROWAWAY ACCOUNT! Nothing interesting here if you get into it

context = ssl.create_default_context()

with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login("mycodeisdone@gmail.com", password)
    server.sendmail('mycodeisdone@gmail.com', 'mycodeisdone@gmail.com', 'The code is done!') # sender, reciever, message
