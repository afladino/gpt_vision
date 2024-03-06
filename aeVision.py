import json,base64,ast,time,aiohttp,asyncio,yaml,os

#* Configuración del ambiente de desarrollo
ENV = os.environ.get('ENVIRONMENT','dev')

class GPTVision():
  def __init__(self) -> None: 
    '''
    Constructor de la clase
    '''
    pass
  
  def load_config(self):
    '''
    Función para cargar la configuración del servicio de IA de comunes
    '''
    with open('./config/config.json', 'r') as file:
        config = json.load(file)
    return config
  
  async def fetch_gptv(self,bs64img_list,session):
    '''
    Función que hace el llamado del modelo GPT-Vision para un (1) riesgo
    '''
    #* Cargar configuración del servicio de GPT-Vision de comunes en AWS
    config = self.load_config()
    endpoint:str = config[ENV]['endpoint']
    headers:dict = config[ENV]['headers']
    act_economica:str = "papeleria"
    zona:str = "Almacenamiento/Exhibición"
    #* Cargar prompt según el tipo de riesgo
    with open('./utils/prompt-template.yaml', 'r') as archivo:
      prompt = yaml.safe_load(archivo)
    prompt = prompt['prompts']['tipos_riesgos']['I']
    PROMPT_SYSTEM:str = prompt.format(act_economica,zona)
    PROMPT_USER:str = "Evalua el riesgo de la(s) fotografia(s)"
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
          # "detail": "high"
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
    async with session.post(url=endpoint, data=json.dumps(payload), headers=headers) as responseGPT:
      response = (await responseGPT.json())     
    with open("./predictions/" + '_response-high' + ".json", "w") as outfile: 
          json.dump(response,outfile,indent = 4)  
    try:
      response = ast.literal_eval(response['data']['choices'][0]['message']['content'].replace('null','None'))
    except Exception as e:
      print(e)
      print(response)
    return response
    
  async def models_caller(self,multiple_imgs,file_name,save):
      '''
      Función que hace el llamado ásincrono del modelo GPT-Vision para múltiples riesgos
      '''
      async with aiohttp.ClientSession() as session:
        tasks = [self.fetch_gptv(imgPack["images"],session) for imgPack in multiple_imgs]
        responses = await asyncio.gather(*tasks)
        if save:
          file_name = file_name.split('.')[0]
          with open("./predictions/" + file_name + ".json", "w") as outfile: 
            json.dump(dict(zip([riesgo["riesgo"] for riesgo in multiple_imgs],responses)),outfile,indent = 4)  
        return json.dumps(dict(zip([riesgo["riesgo"] for riesgo in multiple_imgs],responses)))

#* Función para codificar la imagen en base64
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
      
def main():
  start = time.time()
  fileName = "computador_240x240.jpg"
  tablero = "Tablero_8_240x240.png"
  #* Path to image
  image_path = "./test/" + fileName
  tablero_path = "./test/" + tablero
  #* Getting the base64 string 
  base64_image = encode_image(image_path)
  tablero_image = encode_image(tablero_path)
  cotizacion:list = [
    {
      "riesgo":1,
      "images":[base64_image,tablero_image]
    }
  ]
  #* Llamar al modelo de GPTVision
  model=GPTVision()
  asyncio.run(model.models_caller(multiple_imgs=cotizacion,file_name=fileName,save=True))
  finish = time.time()
  timeEx = finish - start
  print(f'Tiempo de ejecución: {timeEx:.3}')
    
if __name__ == "__main__":
  main()