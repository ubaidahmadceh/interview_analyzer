from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .controllers import *
from django.http import JsonResponse
import json
from .dummy import dummyPatterns,dummyProfiles,dummyAnalysis
import time
import tempfile
import os
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

# Create your views here.

class GetUserProfiles(APIView):
    def post(self,request):
        if request.data:
            data = request.data
            user_data = data.get('data')
            user_id = data.get('userId')
            final_response = process_themes(user_data)
            insights = process_insights(user_data)
            final_response['insight'] = insights['insight']
            summary = process_summary(user_data)
            final_response['summary'] = summary['summary']
            return Response({"response": final_response,'userId': user_id})

        else:
            return Response({'response': 'no data found'})
        

class Chat(APIView):
    def post(self,request):
        data = request.data
        user_data = json.loads(data.get('data'))
        prompt = data.get('question')
        response = chatFunction(user_data, prompt)
        return Response({'answer': response})
    

class Patterns(APIView):
    def post(self,request):
        data = request.data
        input = data.get('data')
        themeComparison = []
        for i in range(len(input)):
            response = getPatterns(input[i])
            themeComparison.append(response)
        time.sleep(10)
        return Response({'response':themeComparison})
    

class OverallAnalysis(APIView):
    def post(self,request):
        data = request.data
        input = data.get('data')
        overall_analysis = []
        obj = input
        prompt1 = f"""
        Act as an AI User Researcher and answer the questions below.
        The text in ``` is from four different users. Build a cohesive summary to take 
        quick insights upto 300 words. Use a coherent and a clear sentence structure and an informative tone.

        text : ```{obj}```
        """
        response =  get_completion(prompt1)
        overall_analysis.append(response)

        prompt2 = f"""
        Act as a product manager and from the overall analysis contained in {response} extract the next actionable steps in a list format in a concise yet descriptive manner.
        text : ```{response}```
        """
        response2 =  get_completion(prompt2)
        overall_analysis.append(response2)
        return Response({'response': overall_analysis})
    

class VoiceTranscription(APIView):
    def post(self,request):
        # files = request.FILES.getlist('file')
        data = request.data
        keys = list(data.keys())
        length = int(len(keys)/2)
        final_response = []

        for i in range(length):
            temp_file = create_temporary_file_with_format(data[f"file-{i}"])
            temp_audio_file = None
            compressed_file = None
            try:
                for chunk in data[f"file-{i}"].chunks():
                    temp_file.write(chunk)

                if get_file_format(temp_file.name) in ['.mov','.avi','.mp4','.mkv']:
                    input_video_path = temp_file.name
                    output_audio_path = tempfile.mktemp(suffix=".mp3")
                    print('1')
                    video = VideoFileClip(input_video_path)
                    print('2')
                    audio = video.audio
                    audio.write_audiofile(output_audio_path)
                    video.close()
                    audio.close()
                    temp_audio_file = open(output_audio_path, 'rb')
                    input_path = temp_audio_file.name
                    output_path = tempfile.mktemp(suffix=".mp3")
                    audio = AudioSegment.from_file(input_path)
                    target_bitrate = '64k'  # For example, 64kbps
                    audio.export(output_path, format='mp3', bitrate=target_bitrate)
                    compressed_file = open(output_path,'rb')
                    transcription = voice_transcription(compressed_file.name)
                    final_response.append({"id":data[f"userId-{i}"],"name": f"user {data[f'userId-{i}']}","value":transcription['text']})
                
                if get_file_format(temp_file.name) in ['.wav', '.mp3', '.m4a', '.mpeg']:
                    input_path = temp_file.name
                    output_path = tempfile.mktemp(suffix=".mp3")
                    audio = AudioSegment.from_file(input_path)
                    target_bitrate = '64k'  # For example, 64kbps
                    audio.export(output_path, format='mp3', bitrate=target_bitrate)
                    compressed_file = open(output_path,'rb')
                    transcription = voice_transcription(compressed_file.name)
                    final_response.append({"id":data[f"userId-{i}"],"name": f"user {data[f'userId-{i}']}","value":transcription['text']})
                    
            except Exception as e:
                return Response({'message': 'Error processing file: ' + str(e)}, status=500)
            finally:
                # Delete the temporary files after processing
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                if temp_audio_file and os.path.exists(temp_audio_file.name):
                    temp_audio_file.close()
                    os.unlink(temp_audio_file.name)
                if compressed_file and os.path.exists(compressed_file.name):
                    compressed_file.close()
                    os.unlink(compressed_file.name)
                
        return Response({ "response": final_response})
