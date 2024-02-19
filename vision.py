import requests
import json
import base64
import ast

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def fetch_gptv(bs64img_list,file_name):
  
  PROMPT_SYSTEM:str = ''''
  Eres un ingeniero experto de riesgos de una compañia aseguradora que evalua vulnerabilidades latentes en un inmueble. Para dicha evaluación sólo cuentas con fotografías del riesgo. Tu objetivo es detectar vulnerabilidades dentro de la fotografía y así generar un concepto de riesgo final para poder apoyar el proceso de suscripción. Proporciona la salida en un formato tipo json con los siguientes campos: [Categoria] [explicacion]
  No incluyas la etiqueta ```json ``` en la salida y el formato del texto debe ser Latin-1.
  '''
  PROMPT_USER:str = ''''
  Califica el siguiente inmueble de acuerdo al riesgo de incendio. Teniendo en cuenta las siguientes categorias. Para ello será proporcionado una foto del interior del inmueble o una foto del tablero electrico o ambas. Realiza la evaluación según la foto proporcionada.

  Alto: La empresa no cuenta con ningún sistema de detección o supresión de incendios, como detectores de humo, sistemas de aspiración, extintores portátiles, sistemas de rociadores automáticos, sistemas de supresión de espuma, alarmas contra incendios o red contra incendios de gabinete con manguera.
  Los materiales de construcción utilizados son altamente inflamables, como paja, madera y asfalto.
  La altura del almacenamiento supera los 6 metros y no hay espacio entre el tope máximo de almacenamiento y el techo del inmueble.
  El tablero eléctrico no cumple con la normatividad técnica RETIE y se observa físicamente deteriorado.
  Se evidencian cables expuestos o defectuosos que pueden generar un riesgo de corto circuito.
  El predio está completamente desordenado, sin demarcación ni separación de sus diferentes áreas.
  No se evidencia un plan de emergencia ni señalización adecuada para la evacuación.
  El material almacenado es de fácil combustión o puede considerarse como una fuente de ignición latente.

  Medio - Alto: La empresa cuenta con mínimo un sistema de detección o supresión de incendios, como detectores de humo, sistemas de aspiración, extintores portátiles, sistemas de rociadores automáticos, sistemas de supresión de espuma, alarmas contra incendios y red contra incendios de gabinete con manguera.
  Los materiales de construcción utilizados no son altamente inflamables, como paja, madera y asfalto.
  La altura del almacenamiento no supera los 6 metros o, en caso de hacerlo, existe un espacio considerable entre el tope máximo de almacenamiento y el techo del inmueble.
  El tablero eléctrico se observa físicamente aceptable.
  No se evidencian cables expuestos o defectuosos que puedan generar un riesgo de corto circuito.
  El predio está parcialmente organizado, con visible separación de sus diferentes áreas.
  Existe un plan de emergencia y señalización adecuada para la evacuación.
  El material almacenado es de combustión media y no se evidencia alguna fuente de ignición latente.

  Medio: La empresa cuenta con dos o más sistemas de detección o supresión de incendios, como detectores de humo, sistemas de aspiración, extintores portátiles, sistemas de rociadores automáticos, sistemas de supresión de espuma, alarmas contra incendios y red contra incendios de gabinete con manguera.
  Los materiales de construcción utilizados son concreto, mampostería o acero.
  La altura del almacenamiento no supera los 6 metros.
  El tablero eléctrico cumple con la normatividad técnica RETIE y se observa en excelente estado.
  No se evidencian cables expuestos o defectuosos que puedan generar un riesgo de corto circuito.
  El predio está totalmente organizado, con demarcación y separación de sus diferentes áreas.
  Existe un plan de emergencia y señalización adecuada para la evacuación.
  El material almacenado es de difícil combustión y no se evidencia alguna fuente de ignición latente.
  
  Medio - Bajo: La empresa cuenta con dos o más sistemas de detección o supresión de incendios, como detectores de humo, sistemas de aspiración, extintores portátiles, sistemas de rociadores automáticos, sistemas de supresión de espuma, alarmas contra incendios y red contra incendios de gabinete con manguera.
  Los materiales de construcción utilizados son concreto, mampostería o acero.
  La altura del almacenamiento no supera los 6 metros.
  El tablero eléctrico cumple con la normatividad técnica RETIE y se observa en excelente estado.
  No se evidencian cables expuestos o defectuosos que puedan generar un riesgo de corto circuito.
  El predio está totalmente organizado, con demarcación y separación de sus diferentes áreas.
  Existe un plan de emergencia y señalización adecuada para la evacuación.
  El material almacenado es de difícil combustión y no se evidencia alguna fuente de ignición latente.

  Bajo: La empresa cuenta con dos o más sistemas de detección o supresión de incendios, como detectores de humo, sistemas de aspiración, extintores portátiles, sistemas de rociadores automáticos, sistemas de supresión de espuma, alarmas contra incendios y red contra incendios de gabinete con manguera.
  Los materiales de construcción utilizados son concreto, mampostería o acero.
  La altura del almacenamiento no supera los 6 metros.
  El tablero eléctrico cumple con la normatividad técnica RETIE y se observa en excelente estado.
  No se evidencian cables expuestos o defectuosos que puedan generar un riesgo de corto circuito.
  El predio está totalmente organizado, con demarcación y separación de sus diferentes áreas.
  Existe un plan de emergencia y señalización adecuada para la evacuación.
  El material almacenado es de difícil combustión y no se evidencia alguna fuente de ignición latente
  '''
  UserContent:list = [
    {
      "type": "text",
      "text": PROMPT_USER
      }
  ]
  for bs64img in bs64img_list:
    imageToInput:dict={
      "type": "image_url",
      "image_url": {
        "url": f"data:image/jpeg;base64,{bs64img}",
        "detail": "high"
        }
      }
    UserContent.append(imageToInput)
    
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
              "content": UserContent
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
  with open("./predictions/" + 'response-high' + ".json", "w") as outfile: 
        json.dump(response.json(),outfile,indent = 4)  
  try:
    response = ast.literal_eval(response.json()['data']['choices'][0]['message']['content'])
    file_name = file_name.split('.')[0]
    with open("./predictions/" + file_name + ".json", "w") as outfile: 
        json.dump(response,outfile,indent = 4)  
  except:
    print(response.json())
        
def main():
  fileName = "comercio_mtto_tecnolog_2948_240x240.png"
  # Path to image
  image_path = "./test/" + fileName
  # Getting the base64 string 
  base64_image = encode_image(image_path)
  # Analize image
  fetch_gptv(bs64img_list=[base64_image],file_name=fileName)
    
if __name__ == "__main__":
  main()