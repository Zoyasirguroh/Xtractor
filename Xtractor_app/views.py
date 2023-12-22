from django.shortcuts import render
import requests
from django.http import JsonResponse
import json
from django.core.files.storage import FileSystemStorage
fs = FileSystemStorage()
import os   
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view


# from .serializers import FilePathSerializer
import pandas as pd
import fitz
import pdfplumber
import re

# myapp/views.py
from rest_framework.parsers import FileUploadParser
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.views import View

from .models import File
from .serializers import FileSerializer
from django.http import HttpResponse
from django.views.decorators.http import require_POST, require_GET


# get nearest words in the given lines into same bbox
def group_nearest_words(line_bboxes, h_threshold = 15):
  formatted_line_bboxes = []
  for line in line_bboxes: # boxes in the lines are horizontally sorted
    # print("line_bbox",line)
    formatted_line = []
    current_words = [line[0]]
    # print("current_words",current_words)
    for i, word in enumerate(line[1:]):

      if abs(word["bbox"][0] - current_words[-1]["bbox"][2]) < h_threshold:
        current_words.append(word)
      else: # mayn't reaches to end words
        formatted_line.append(current_words)
        current_words = [word]

      if i == len(line[1:]) - 1 and current_words not in formatted_line: # if it reaches to end words
        formatted_line.append(current_words)

    formatted_line_bboxes.append(formatted_line)

  return formatted_line_bboxes

def group_bboxes_by_lines(bboxes, threshold=10):
    grouped_lines = []
    current_line = [bboxes[0]]
    is_parsed = [bboxes[0]]

    for bbox in bboxes[0:]:
        if abs(bbox["bbox"][1] - current_line[-1]["bbox"][1]) < threshold:
            current_line.append(bbox)
        else:
            grouped_lines.append(current_line)
            current_line = [bbox]

    grouped_lines.append(current_line)
    return grouped_lines


    grouped_lines.append(current_line)
    return grouped_lines

# Get common bbox for the neighbor words
def get_common_bbox_for_neighbors(formatted_line_bboxes):
  formatted_lines = []
  for line in formatted_line_bboxes:
    formatted_line = []
    for neighbor_words in line:
      text = neighbor_words[0]["text"]
      x_min, y_min, x_max, y_max = neighbor_words[0]["bbox"]
      if len(neighbor_words) > 1:
        for word in neighbor_words[1:]:
          x1, y1, x2, y2 = word["bbox"]
          # update common bbox
          x_min, y_min = min(x1, x_min), min(y1, y_min)
          x_max, y_max = max(x2, x_max), max(y2, y_max)
          text += " "+ word["text"]
      formatted_line.append({"text":text, "bbox":[x_min, y_min, x_max, y_max]})

    formatted_lines.append(formatted_line)

  return formatted_lines

def extract_text_from_pdf(input_pdf):
    # Open the PDF file
    pdf_document = fitz.open(input_pdf)

    # Initialize an empty string to store the extracted text
    extracted_text = ""

    # Iterate through all pages
    for page_number in range(pdf_document.page_count):
        # Get the page
        page = pdf_document[page_number]

        # Extract text from the page
        page_text = page.get_text("text")

        # Append the text to the result
        extracted_text += f"\nPage {page_number + 1}:\n{page_text}\n"

    # Close the PDF file
    pdf_document.close()

    return extracted_text
def has_only_one_word(sentence):
    # Split the sentence into words
    words = sentence.split()

    # Check if there is only one word
    return len(words) == 1

from django.http import HttpResponse

# views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import FileUploadForm
from django.core.files.storage import default_storage

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            file_path = default_storage.save(f'media/{uploaded_file.name}', uploaded_file)
            cwd = os.getcwd()
            input_pdf = os.path.join(cwd, 'media',file_path)
            with pdfplumber.open(input_pdf) as pdf:
              document_info = dict()
              print(pdf.pages)
              for i,page in enumerate(pdf.pages):
                word_bboxes = []
                words = page.extract_words()
                for word in words:
                  text = word["text"]
                  bbox = [word["x0"], word["top"], word["x1"], word["bottom"]]  # Bounding box: (left, top, right, bottom)
                  word_bboxes.append({"text": text, "bbox": bbox})
                document_info[i] = {"document":word_bboxes, "dimension":[page.width, page.height]}
            df = pd.DataFrame(columns=["key", "value"])
            for j in range(len(pdf.pages)):
                print("page number",j)
                width, height = document_info[j]["dimension"]
                page_document_info = document_info[j]["document"]
                page_document_info_sorted = sorted(page_document_info, key = lambda z:(z["bbox"][1], z["bbox"][0]))
                line_bboxes = group_bboxes_by_lines(page_document_info_sorted)
                formatted_line_bboxes = group_nearest_words(line_bboxes)
                formatted_lines = get_common_bbox_for_neighbors(formatted_line_bboxes)
                kv_threshold = 50
                extracted_infos = []
                for i,line in enumerate(formatted_lines):
                  if len(line) == 0 : # there is no key-value pairs in the line
                    pass
                  elif len(line)==1 and len(formatted_lines[i+1])>1:
                    main_key = line[0]['bbox'][0]
                    key = formatted_lines[i+1][0]['bbox'][0]
                    if len(formatted_lines[i+1])==2:
                      val = formatted_lines[i+1][1]['bbox'][0]
                      if main_key == key:
                        key_values = {
                            "key": line[0]['text'],
                            "value": " "
                        }
                        extracted_infos.append(key_values)
                        new_row = {"key":line[0]['text'], "value": " "}
                        df1= pd.DataFrame(new_row, index=[0])
                        df = pd.concat([df, df1])
                      elif main_key == val:
                        key_values = {
                            "key": "  " ,
                            "value": line[0]['text']
                        }
                        extracted_infos.append(key_values)
                        new_row = {"key":"  ", "value": line[0]['text']}
                        df1= pd.DataFrame(new_row, index=[0])
                        df = pd.concat([df, df1])
                  elif len(line)>1 and abs(line[1]["bbox"][0] - line[0]["bbox"][2]) > kv_threshold and line[1]["bbox"][0]:
                    key_values = {
                        "key": line[0]['text'],
                        "value": line[1]['text']
                    }
                    extracted_infos.append(key_values)
                    print("\n\n\n\n")
                    print(extracted_infos)
                    new_row = {"key":line[0]['text'], "value": line[1]['text']}
                    df1= pd.DataFrame(new_row, index=[0])
                    df = pd.concat([df, df1])
            result = extract_text_from_pdf(input_pdf)
            for i in range(len(df)-1):
              value_str = str(df['value'].iloc[i])
              if 'key' in df.columns and i + 1 < len(df):
                  key_str = str(df['key'].iloc[i + 1])
              else:
                  key_str = "" 
              value_str_escaped = re.escape(value_str)
              key_str_escaped = re.escape(key_str)
              pattern = re.compile(value_str_escaped + r'(\n.*?\n)' + key_str_escaped, re.DOTALL)
              match = pattern.search(result)
              if match:
                extracted_text = match.group(1).strip()
                if has_only_one_word(extracted_text):
                  print(extracted_text)
                  new_row = {"key":extracted_text,"value":" " }
                  insert_index = i+1
                  df.loc[insert_index + 1:] = df.loc[insert_index:].shift(1)
                  df.loc[insert_index] = new_row
                  df.reset_index(drop=True, inplace=True)
              else:
                  print("No match found.")
            # for i in range(len(df)-1):
            #   print(df["key"].iloc[i])
            #   if df["key"].iloc[i].isspace():
            #     df["value"][i-1] = df["value"][i-1] + " "+df["value"][i]
            #     df = df.drop(i)
            i = 0
            while i < len(df) - 1:
                print(df["key"].iloc[i])
                
                if df["key"].iloc[i].isspace():
                    df["value"][i-1] = df["value"][i-1] + " " + df["value"][i]
                    df = df.drop(i).reset_index(drop=True)
                else:
                    i += 1
            df.reset_index(drop=True, inplace=True)
            dict_of_dicts = df.to_dict(orient='index')
            print(dict_of_dicts)
        return JsonResponse(dict_of_dicts)
            # Process and save the file as needed
            # You can use Django's File storage API or save it to the database, etc.
        #     return JsonResponse({'message': 'File uploaded successfully.'})
        # else:
        #     return JsonResponse({'message': 'Invalid form data.'}, status=400)
    else:
        return JsonResponse({'message': 'Invalid request method.'}, status=400)


class FilePathView(View):
    parser_classes = [MultiPartParser, FormParser]
    
    @csrf_exempt
    @api_view(['POST'])
    def post(self, request, *args, **kwargs):
        file_serializer = FileSerializer(data=request.data)

        if file_serializer.is_valid():
            file_serializer.save()
            file_path = "C:\\Users\\zuhrah.sirguroh\\Downloads\\ocr\\SET1\\companyextract-Botswana_Insurance_Company_Limited-BW00000868164.pdf"
            print(file_path)
            input_pdf = file_path
            with pdfplumber.open(input_pdf) as pdf:
              document_info = dict()
              print(pdf.pages)
              for i,page in enumerate(pdf.pages):
                word_bboxes = []
                words = page.extract_words()
                for word in words:
                  text = word["text"]
                  bbox = [word["x0"], word["top"], word["x1"], word["bottom"]]  # Bounding box: (left, top, right, bottom)
                  word_bboxes.append({"text": text, "bbox": bbox})
                document_info[i] = {"document":word_bboxes, "dimension":[page.width, page.height]}
            df = pd.DataFrame(columns=["key", "value"])
            for j in range(len(pdf.pages)):
                width, height = document_info[j]["dimension"]
                page_document_info = document_info[j]["document"]
                page_document_info_sorted = sorted(page_document_info, key = lambda z:(z["bbox"][1], z["bbox"][0]))
                line_bboxes = group_bboxes_by_lines(page_document_info_sorted)
                formatted_line_bboxes = group_nearest_words(line_bboxes)
                formatted_lines = get_common_bbox_for_neighbors(formatted_line_bboxes)
                kv_threshold = 50
                extracted_infos = []
                for i,line in enumerate(formatted_lines):
                  if len(line) == 0 : # there is no key-value pairs in the line
                    pass
                  elif len(line)==1 and len(formatted_lines[i+1])>1:
                    main_key = line[0]['bbox'][0]
                    key = formatted_lines[i+1][0]['bbox'][0]
                    if len(formatted_lines[i+1])==2:
                      val = formatted_lines[i+1][1]['bbox'][0]
                      if main_key == key:
                        key_values = {
                            "key": line[0]['text'],
                            "value": " "
                        }
                        extracted_infos.append(key_values)
                      elif main_key == val:
                        key_values = {
                            "key": "  " ,
                            "value": line[0]['text']
                        }
                        extracted_infos.append(key_values)
                  elif len(line)>1 and abs(line[1]["bbox"][0] - line[0]["bbox"][2]) > kv_threshold and line[1]["bbox"][0]:
                    key_values = {
                        "key": line[0]['text'],
                        "value": line[1]['text']
                    }
                    extracted_infos.append(key_values)
            for i in range(len(extracted_infos)):
              new_row = {"key":extracted_infos[i]["key"], "value": extracted_infos[i]["value"]}
              df1= pd.DataFrame(new_row, index=[0])
              df = pd.concat([df, df1])
            result = extract_text_from_pdf(input_pdf)
            for i in range(len(df)-1):
              value_str = str(df['value'].iloc[i])
              if 'key' in df.columns and i + 1 < len(df):
                  key_str = str(df['key'].iloc[i + 1])
              else:
                  key_str = "" 
              value_str_escaped = re.escape(value_str)
              key_str_escaped = re.escape(key_str)
              pattern = re.compile(value_str_escaped + r'(\n.*?\n)' + key_str_escaped, re.DOTALL)
              match = pattern.search(result)
              if match:
                extracted_text = match.group(1).strip()
                if has_only_one_word(extracted_text):
                  print(extracted_text)
                  new_row = {"key":extracted_text,"value":" " }
                  insert_index = i+1
                  df.loc[insert_index + 1:] = df.loc[insert_index:].shift(1)
                  df.loc[insert_index] = new_row
                  df.reset_index(drop=True, inplace=True)
              else:
                  print("No match found.")
            for i in range(len(df)-1):
              if df["key"].iloc[i].isspace():
                df["value"][i-1] = df["value"][i-1] + " "+df["value"][i]
                df = df.drop(i)
            df.reset_index(drop=True, inplace=True)
            dict_of_dicts = df.to_dict(orient='index')
            print(dict_of_dicts)
        return JsonResponse(dict_of_dicts)

        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

def Uploadfiles(request):
    return render(request, 'index.html')