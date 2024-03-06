import json,base64,ast,time,requests,os

#* Configuración del ambiente de desarrollo
ENV = os.environ.get('ENVIRONMENT','dev')

def load_config():
    '''
    Función para cargar la configuración del servicio de IA de comunes
    '''
    with open('./config/config.json', 'r') as file:
        config = json.load(file)
    return config

def fetch(bs64img_list):
    '''
    Función que hace el llamado al modelo de GPTVision de comunes
    '''
    config = load_config()
    endpoint:str = config[ENV]['endpoint']
    headers:dict = config[ENV]['headers']
    PROMPT_SYSTEM:str = """
    Eres un ingeniero financiero experto. Tu tarea es extraer los datos de las variables financieras de un estado financiero a partir de una imagen. Extrae las siguientes variables financieras y proporciona un salida en formato JSON, discriminado por año:
        - [activo_corriente]
        - [activo_no_corriente]
        - [total_pasivos]
        - [patrimonio]
        - [total_pasivo_patrimonio]
    No incluyas la etiqueta ```json ``` en la salida y no incluyas recomendaciones.
    """
    PROMPT_USER:str = "Extrae la información del siguiente estado financiero"
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
          #"detail": "high"
          }
        }
      UserContent.append(imageToInput)
    payload = {
        "iaType": "azure",
        "portal": "patrimoniales",
        "data": {
            "model": "PATRIM-GPT4V",
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
    response = requests.post(url=endpoint, data=json.dumps(payload), headers=headers)
    response = response.json()  
    with open("./predictions/" + 'documentExtractorResponse' + ".json", "w") as outfile: 
        json.dump(response,outfile,indent = 4)  
    try:
      response = ast.literal_eval(response['data']['choices'][0]['message']['content'])
      with open("./predictions/" + 'documentExtractor' + ".json", "w") as outfile: 
          json.dump(response,outfile,indent = 4)  
    except Exception as e:
      print(e)
      print(response)
    return response

def encode_image(image_path):
    '''
    Convierte una imagen en formato Base64
    '''
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    fileName = "estados_financieros.png"
    image_path = "./test/" + fileName
    #* Getting the base64 string 
    base64_image = encode_image(image_path)
    fetch(bs64img_list=[base64_image])
    
if __name__ == "__main__":
    main()
    