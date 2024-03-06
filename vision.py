import json,base64,ast,time,aiohttp,asyncio,yaml,os,numpy,math
from fastapi import HTTPException

#* Configuración del ambiente de desarrollo
ENV = os.environ.get('ENVIRONMENT','dev')

class GPTVision():
  def __init__(self,env,cod_actividad) -> None: 
    '''
    Constructor de la clase
    '''
    self.env = env
    self.cod_actividad = cod_actividad
  
  def load_config(self):
    '''
    Función para cargar la configuración del servicio de IA de comunes
    '''
    with open('./config/config.json', 'r') as file:
        config = json.load(file)
    return config
  
  async def fetch_gptv(self,bs64img_list,zonas):
    '''
    Función que hace el llamado del modelo GPT-Vision para un (1) riesgo
    '''
    codActividades = {
      "03009":"Artículos Domésticos", #!
      "01001":"Centros Médicos y Veterinarios" , #!
      "01001":"Comercio Alimentos", #! Repetido en BD 02000
      "03001":"Comercio Autopartes", #!
      "03006":"Comercio Farmacéuticos", #!
      "03002":"Comercio Ferretería y Materiales Construcción", #! Repetido en BD 03004
      "03003":"Comercio Mtto Tecnología", #!
      "03005":"Comercio Ropa", #!
      "04001":"Fabricas", #! Repetido en BD 04000
      "11001":"Industria Metalmecánica", #! Repetido en BD 11000
      "05001":"Oficinas", #! Repetido en BD 05000
      "03007":"Papelerías", #! 
      "06001":"Restaurantes", #! Repetido en BD 06000
      "07001":"Servicios Alojamiento", #! Repetido en BD 07000
      "09001":"Servicios Educativos", #! Repetido en BD 09000
      "01002":"Servicios Estéticos", #!
      "08001":"Taller Automotriz" #! Repetido en BD 08000
      } 
    #* Cargar configuración del servicio de GPT-Vision de comunes en AWS
    config = self.load_config()
    endpoint:str = config[self.env]['endpoint']
    headers:dict = config[self.env]['headers']
    #TODO: Toca definir las zonas
    zonasIncendio:str = "Fachada - Zona de trabajo"
    zonasElectrico:str = "Tablero Electrico"
    #* Cargar prompt según el tipo de riesgo
    with open('./utils/prompt-template.yaml', 'r') as archivo:
      prompt = yaml.safe_load(archivo)
    prompt = prompt['prompts']['tipos_riesgos'][self.cod_actividad]
    PROMPT_SYSTEM:str = prompt.format(codActividades.get(self.cod_actividad,"Empresa"),zonasIncendio,zonasElectrico)
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
    async with aiohttp.ClientSession() as session:
      try:
        async with session.post(url=endpoint, data=json.dumps(payload), headers=headers) as responseGPT:
          response = (await responseGPT.json())
          with open("./predictions/full_response.json", "w") as outfile: 
            json.dump(response,outfile,indent = 4)  
          if responseGPT.status == 200:
            response = ast.literal_eval(response['data']['choices'][0]['message']['content'].replace('null','None'))
          else:
            #TODO: Definir qué enviar cuando la respuesta no es exitosa
            response = {"data":f"Entidad no procesable: {response['description']}"}
          response.update({"status_code":responseGPT.status})
          return response
      except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error de cliente: {e}")
    
  async def models_caller(self,multiple_imgs):
      '''
      Función que hace el llamado ásincrono del modelo GPT-Vision para múltiples riesgos
      '''
      zonas = [[zona["zona"] for zona in riesgo["imagenes"]] for riesgo in multiple_imgs["riesgos"]]
      imgPack = [[img["img"] for img in riesgo["imagenes"]] for riesgo in multiple_imgs["riesgos"]]
      riesgos = [riesgo['riesgo_id'] for riesgo in multiple_imgs['riesgos']]
      tasks = [self.fetch_gptv(imgs,zonas) for imgs,zonas in zip(imgPack,zonas)]
      responses = await asyncio.gather(*tasks)
      return dict(zip(riesgos,responses))
    
  def compute_scores(self,prediction,save):
    '''
    Función que promedia los variables de cada tipo de riesgo
    '''
    predictionScored = prediction.copy()
    num_riesgos = len(predictionScored.keys())
    tipoRiesgos = ["riesgo_electrico","riesgo_incendio"]
    #* Crear una matriz para almacenar los promedios de n*m, donde n=Riesgo y m=Tipo riesgo
    scoresMatrix = numpy.zeros(shape=(num_riesgos,len(tipoRiesgos)),dtype=numpy.float64)
    for idxRiesgo,numRiesgo in enumerate(predictionScored):
      for idxTipoRiesgo,tipoRiesgo in enumerate(tipoRiesgos):
        if predictionScored[numRiesgo]["status_code"] == 200:
          #* Generar el vector de las calificaciones sin tomar la variable "justificacion" y las variables que sean None
          varsCalificaciones = numpy.array([v for v in list(predictionScored[numRiesgo][tipoRiesgo].values())[:-1] if v is not None],dtype=numpy.float64)
          scoreRiesgo = varsCalificaciones.mean() if len(varsCalificaciones) > 0 else None 
          #* Asignar el Score de riesgo promedio por cada tipo de riesgo e incluir dentro de matriz  
          predictionScored[numRiesgo][tipoRiesgo]['score_riesgo'] = scoreRiesgo
          scoresMatrix[idxRiesgo,idxTipoRiesgo] = scoreRiesgo
        else:
          scoresMatrix[idxRiesgo,idxTipoRiesgo] = None
    # print(scoresMatrix)
    #* Realiza el promedio de los scores de cada riesgo para generar un score global
    predictionScored['riesgo_electrico_global'] = None if math.isnan(numpy.nanmean(scoresMatrix[:, 0])) else numpy.nanmean(scoresMatrix[:, 0]) 
    predictionScored['riesgo_incendio_global'] = None if math.isnan(numpy.nanmean(scoresMatrix[:, 1])) else numpy.nanmean(scoresMatrix[:, 1]) 
    if save:
      with open("./predictions/responseGPTV.json", "w") as outfile: 
        json.dump(predictionScored,outfile,indent = 4)  
    return predictionScored

def encode_image(image_path):
  '''
  Convierte una imagen en formato base64
  '''
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def main():
  start = time.time()
  fileName = "fachada_metalmecanica.jpg"
  tablero = "Tablero_8_240x240.png"
  #* Path to image
  image_path = "./test-2/" + fileName
  tablero_path = "./test/" + tablero
  image_path2 = "./test-2/produccion_metalmecanica.png"
  #* Getting the base64 string 
  base64_image = encode_image(image_path)
  tablero_image = encode_image(tablero_path)
  base64_image2 = encode_image(image_path2)
  cotizacion:dict = {
    "codigo_ae":"11001",
    "riesgos":[
      {
        "riesgo_id":"AAA",
        "imagenes":[
          {
            'img':base64_image,
            'zona':'Fachada'
            },
          {
            'img':base64_image2,
            'zona':'Zona de trabajo'
            },
          {
            'img':tablero_image,
            'zona':'Tablero'
            }
          ]
        },      
      ]
    }  
  #* Llamar al modelo de GPTVision
  model=GPTVision(env=ENV,cod_actividad=cotizacion['codigo_ae'])
  runModel:bool=True
  if runModel:
    prediction = asyncio.run(model.models_caller(multiple_imgs=cotizacion))
  else:
    with open('./predictions/computador_240x240.json', 'r') as resposeFile:
      prediction = json.load(resposeFile)
  predictionComputed = model.compute_scores(prediction,save=True)
  print(predictionComputed)
  finish = time.time()
  timeEx = finish - start
  print(f'Tiempo de ejecución: {timeEx:.3}')
    
if __name__ == "__main__":
  main()