from cryptography.fernet import Fernet       #for encryption and decryption
from PIL import Image                        #for opening and extracting pixels from image
import numpy as np              
import os.path
from os import path
import sys
import getpass                               #for secure input of key
from tqdm import tqdm                        #for progress bar

Image.MAX_IMAGE_PIXELS=None

class image_stg:

'''Fernet key'''

    def __init__(self,key):
        self.f=Fernet(key)

'''function for encryption'''

    def encrypt(self,data):
        enc_data=self.f.encrypt(data)
        return enc_data+b'^'

'''function of decryption'''

    def decrypt(self,enc_data):
        data=self.f.decrypt(enc_data)
        return data

'''read file data'''

    def read_data(self,path):
        with open(path,"rb") as f:
            data=f.read()
        return data

'''write data into file'''

    def write_data(self,path,data):
        with open(path,"wb") as f:
            f.write(data)

'''Convert bytes into binary'''

    def bytes_to_binary(self,byte_buffer):
        print("Converting Bytes to Binary:")
        bar=tqdm(total=len(byte_buffer))
        bin_buffer=""
        for i in byte_buffer:
            tmp="{0:b}".format(i)
            if len(tmp)==6:
                tmp='0'+tmp
            bar.update(1)
            bin_buffer=bin_buffer+tmp
        return bin_buffer

'''Convert binary into bytes'''

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

'''Calculate the number of bits available to embed data'''

    def calc_bytes(self,img):
        width,height=img.size
        size=3*width*height
        return size

'''Embed binary data into image
using numpy edit pixel data to replace LSB with the binary data of the embed file'''

    def img_embed(self,bin_data,output_dir):
        img=Image.open("temp.png")
        size=self.calc_bytes(img)
        if len(bin_data)>=size:
            print("Embed file is too Big !\nEmbed file must be less than {} Bytes".format((size/8)))
            sys.exit()
        im_arr=np.array(img)
        shape=im_arr.shape
        bin_arr=np.array(list(bin_data),dtype=int)
        bin_arr=bin_arr.reshape(bin_arr.shape[0],1)
        img_num=im_arr.reshape(np.product(im_arr.shape),1)
        bin_img=np.unpackbits(img_num,axis=1)
        temp_bin=bin_img[:,7]
        bar=tqdm(total=bin_arr.shape[0])
        print("Embedding Data:")

        for i in range(bin_arr.shape[0]):
            temp_bin[i]=bin_arr[i]
            bar.update(1)

        temp_bin=temp_bin.reshape(temp_bin.shape[0],1)
        bin_img=np.delete(bin_img,7,1)
        bin_img=np.concatenate((bin_img,temp_bin),axis=1)
        new_img_num=np.packbits(bin_img)
        new_img_num=new_img_num.reshape(new_img_num.shape[0],1)
        new_img=new_img_num.reshape(shape)
        new_im=Image.fromarray(new_img)
        new_im.save(os.path.join(output_dir,"emb_img.png"),quality=100)

'''Extract data by accessing the LSB of every color in every pixel''' 

    def img_extract(self,img):
        print("Extracting....")
        bin_buffer=""
        num=np.array(img)
        num=num.reshape(np.product(num.shape),1)
        bin_num=np.unpackbits(num,axis=1)
        bin_num=np.delete(bin_num,(0,1,2,3,4,5,6),1)
        bin_num=np.ravel(bin_num)
        bin_num=bin_num.tolist()
        bin_buffer=''.join(map(str,bin_num))
        return bin_buffer

'''converts images to png'''

def converter(path):
    try:
        img=Image.open(path)
        img.save("temp.png")
    except:
        print("Invalid Carrier File")
        sys.exit()

'''checks wether the given file or folder exists'''

def check_path(path,index,out):
    if index==0:
        if(not os.path.isdir(path)):
            print(out)
            sys.exit()
    elif index==1:
        if(not os.path.isfile(path)):
            print(out)
            sys.exit()

'''sets the output directory if the user has not specified any output'''

def set_output_dir(arglist):
    output_dir=os.getcwd()
    if len(arglist)==5 and os.path.isdir(arglist[4]):
        output_dir=arglist[4]
    else:
        print("Output Directory not specified or Invaid\nUsing Current Directory as Output Directory")
    return output_dir

'''function to call all fucntions required to embed data sequentially'''

def embed(arglist):
    output_dir=set_output_dir(arglist)
    check_path(arglist[2],1,"Invalid Carrier File")
    check_path(arglist[3],1,"Invalid Embed File")
    key=Fernet.generate_key()
    im=image_stg(key)
    enc_bytes=im.bytes_to_binary(im.encrypt(im.read_data(arglist[3])))
    converter(arglist[2])
    im.img_embed(enc_bytes,output_dir)
    os.remove("temp.png")
    with open(os.path.join(output_dir,"key.txt"),'w') as f:
        f.write(key.decode())

'''function to call all functions required to extract embedded data'''

def extract(arglist):
    output_dir=set_output_dir(arglist)
    check_path(arglist[2],1,"Invalid Carrier File")
    im=image_stg(getpass.getpass(prompt="Key:"))
    emb_img=Image.open(arglist[2])
    bin_buff=im.img_extract(emb_img)
    byte_buff=im.binary_to_bytes(bin_buff).encode()
    dec_data=im.decrypt(byte_buff)
    with open(os.path.join(output_dir,"dec_data.{}".format(arglist[3])),"wb") as f:
        f.write(dec_data)

'''displays the usage'''

def helper():
    print("\n\nUsage:\n\n\tcryptsteg -emb <Path to Carrier Image> <Path to Embed File> <Output Path default=current directory>\n\tcryptsteg -ext <Path to Carrier Image> <Embedded Data Format> <Output Path default=current directory>\n\nExample:\n\n\tcryptsteg -emb image.png file.txt\n\tcryptsteg -ext image.png txt\n\n")

if __name__=="__main__":
    arglist=sys.argv
    if len(arglist) < 4:
        helper()
        sys.exit()
    embed(arglist) if arglist[1]=='-emb' else extract(arglist) if arglist[1]=='-ext' else helper()
    
