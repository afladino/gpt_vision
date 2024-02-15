import requests
import json
import base64
import ast
import sys

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

file_name = "metalmecanica_920x920.png"

# Path to your image
image_path = "./test/" + file_name

# Getting the base64 string 
base64_image = encode_image(image_path)

cobertura:str='incendio'
PROMPT_SYSTEM:str = ''''
Eres un ingeniero experto de riesgos de una compañia aseguradora que evalua vulnerabilidades latentes en un inmueble. Para dicha evaluación sólo cuentas con fotografías del riesgo. Tu objetivo es detectar vulnerabilidades dentro la fotografía y así generar un concepto de riesgo final para poder apoyar el proceso de suscripción. Proporciona la salida en un formato tipo json con los siguientes campos: [Categoria] [explicacion]
'''
PROMPT_USER:str = ''''
Califica el siguiente inmueble de acuerdo al riesgo de incendio. Teniendo en cuenta las siguientes categorias:
Alto: No se evidencia protecciones contra incendio. No se evidencie espacio considerable entre la zona de almacenamiento y el techo (2 metros al menos). Y se evidencia que los materiales de la edificación es de madera.
Medio: Se evidencian protecciones parciales contra incendio. Existe espacio considerable entre la zona de almacenamiento y el techo (2 metros al menos). Y se evidencia que los materiales de la edificación no son de madera.
Bajo: Cuenta con todas las protecciones anti incendio. La zona de almacenamiento esta correctamente demarcada, organizada y apilada y adicionalmente esta alejada del techo. Y los materiales de la edificación son de concreto.
'''
payload = {
    "iaType": "azure",
    "portal": "patrimoniales",
    "data": {
        "model": "PATRIM-GPT4V",
        # "gpt-3.5-turbo-16k"
        # variable: PATRIM-GPT3516K
        "messages": [
          {
            "role": "system",
            "content": PROMPT_SYSTEM
            },
          {
            "role": "user",
            "content": [
              {
                "type": "text",
                "text": PROMPT_USER
                },
              {
                "type": "image_url",
                "image_url": {
                  "url": f"data:image/jpeg;base64,{base64_image}"
                  }
                }
              ]
            }
        ],
        "max_tokens": 1200,
        "temperature": 0,
        "top_p": 1
    }
}
headers = {
    'channel': 'cc',
    'invoke-date': '2023-11-22T15:30:00',
    'enviroment_channel': 'DEV',
    'x-api-key': 'hYLeN3f3L82V6JzGeDmZw2AmW5XS2UOF6YXakKZp'
    
}
response = requests.post(url='https://fz73xehwah.execute-api.us-east-1.amazonaws.com/dev/modelos_ia/api/v1/providers',
                         headers=headers,
                         data=json.dumps(payload))

response = ast.literal_eval(response.json()['data']['choices'][0]['message']['content'].replace('json','').replace('`',''))

file_name = file_name.split('.')[0]

with open("./predictions/" + file_name + ".json", "w") as outfile: 
    json.dump(response,outfile,indent = 4)  