from cryptography.fernet import Fernet
import json
from flask import Flask,render_template,request,Response
from flaskwebgui import FlaskUI
from PIL import Image
import numpy as np
import os.path
from os import path
import sys
import easygui
Image.MAX_IMAGE_PIXELS=None

path_dict={}

app=Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
ui=FlaskUI(app)

class image_stg:

    def __init__(self,key):
        self.f=Fernet(key)

    def encrypt(self,data):
        enc_data=self.f.encrypt(data)
        return enc_data+b'^'

    def decrypt(self,enc_data):
        data=self.f.decrypt(enc_data)
        return data

    def read_data(self,path):
        with open(path,"rb") as f:
            data=f.read()
        return data
    
    def write_data(self,path,data):
        with open(path,"wb") as f:
            f.write(data)

    def bytes_to_binary(self,byte_buffer):
        bin_buffer=""
        for i in byte_buffer:
            tmp="{0:b}".format(i)
            if len(tmp)==6:
                tmp='0'+tmp
            bin_buffer=bin_buffer+tmp
        return bin_buffer

    def binary_to_bytes(self,bin_buffer):
        byte_buffer=""
        i=0
        length=len(bin_buffer)
        while i<int(len(bin_buffer)):
            tmp=bin_buffer[i:i+7]
            if tmp[0]=='0':
                tmp=tmp[1:7]
            try:
                tmp=chr(int(str(tmp),2))
            except:
                pass
            if tmp!='^':
                byte_buffer=byte_buffer+tmp
                i=i+7
            else:
                break
        return byte_buffer

    def calc_bytes(self,img):
        width,height=img.size
        size=3*((width*height)/8)
        return size

    def prepare_sample(self,para):
        temp_sample="{0:b}".format(para)
        temp_sample=temp_sample[0:(len(temp_sample)-1)]
        return temp_sample

    def img_embed(self,img,bin_data):
        print("Embedding Image......")
        im_arr=np.array(img)
        shape=im_arr.shape
        bin_arr=np.array(list(bin_data),dtype=int)
        bin_arr=bin_arr.reshape(bin_arr.shape[0],1)
        img_num=im_arr.reshape(np.product(im_arr.shape),1)
        bin_img=np.unpackbits(img_num,axis=1)
        temp_bin=bin_img[:,7]

        for i in range(bin_arr.shape[0]):
            temp_bin[i]=bin_arr[i]

        temp_bin=temp_bin.reshape(temp_bin.shape[0],1)
        bin_img=np.delete(bin_img,7,1)
        bin_img=np.concatenate((bin_img,temp_bin),axis=1)
        new_img_num=np.packbits(bin_img)
        new_img_num=new_img_num.reshape(new_img_num.shape[0],1)
        new_img=new_img_num.reshape(shape)
        new_im=Image.fromarray(new_img)
        new_im.save("output/enc_output.png",quality=100)
    
    def img_extract(self,img):
        print("Extracting Embedded Data...........")
        num=np.array(img)
        num=num.reshape(np.product(num.shape),1)
        bin_num=np.unpackbits(num,axis=1)
        bin_num=np.delete(bin_num,(0,1,2,3,4,5,6),1)
        bin_num=np.ravel(bin_num)
        bin_num=bin_num.tolist()
        self.bin_buffer=''.join(map(str,bin_num))
        
def hide():
    try:
        img_path=path_dict["hide_im_path"]
        img=Image.open(img_path)
    except:
        return "Invalid Image File"
    em_path=path_dict["hide_em_path"]
    if(not os.path.isfile(em_path)):
        return "Invalid Embed File"
    img=img.convert('RGB')
    key=Fernet.generate_key() 
    img_stg=image_stg(key)
    size=img_stg.calc_bytes(img)
    if size<=os.path.getsize(em_path):
        return "The embed file is too big ! Select a file of size less than {} Bytes".format(size)
    data=img_stg.read_data(em_path)
    a=img_stg.encrypt(data)
    bin_a=img_stg.bytes_to_binary(a)
    img_stg.img_embed(img,bin_a)
    with open("output/key.txt","w") as f:
        f.write(key.decode())
    return "Successful! The key is in the output directory"

def show():
    if(not os.path.isfile(path_dict["show_im_path"])):
        return "Invalid Embed File"
    enc_path=path_dict["show_im_path"]
    format_output=path_dict["format"]
    key=path_dict["dec_key"]
    try:
        img_stg=image_stg(key)
    except:
        return "Decryption Failed !"
    enc_img=Image.open(enc_path)
    img_stg.img_extract(enc_img)
    byte_buff=img_stg.binary_to_bytes(img_stg.bin_buffer)
    b=img_stg.decrypt(byte_buff.encode())
    img_stg.write_data("output/output.{}".format(format_output),b)
    return "Extracted to output directory"

def storage(flag,data):
    if data=='' or data==None:
        return -1
    else:
        path_dict[flag]=data
        return 0

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/handle",methods=['POST'])
def req():
    data=request.get_json(force=True)
    if "hide" in data.keys():
        if "im_path" in data.values():
            res=storage("hide_im_path",easygui.fileopenbox(default="*.png"))
            return str(res)
        elif "em_path" in data.values():
            res=storage("hide_em_path",easygui.fileopenbox(default="*.*"))
            return str(res)
    elif "show" in data.keys():
        res=storage("show_im_path",easygui.fileopenbox(default="*.png"))
        return str(res)
    elif "dec_key" in data.keys():
        res=storage("dec_key",data["dec_key"])
        return str(res)
    elif "format" in data.keys():
        res=storage("format",data["format"])
        return str(res)
    if "init" in data.keys():
        if "hide" in data.values():
            result=hide()
            return result
        elif "show" in data.values():
            result=show()
            return result
   
if __name__ == "__main__": 
    ui.run()
