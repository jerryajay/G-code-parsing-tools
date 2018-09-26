from tqdm import tqdm
import requests

if __name__ == "__main__":

    file_index = 816121

    while file_index <= 817120:
        response = requests.get('http://www.thingiverse.com/thing:'+str(file_index)+'/zip', stream=True, headers={'User-agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            with open("/home/jerry/Desktop/STL-files/"+str(file_index)+".zip", "wb") as handle:
                handle.write(response.content)
            print "Downloaded:", str(file_index)+".zip"
            file_index += 1
        else:
            file_index += 1
            continue

    print "Done"
