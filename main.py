import requests
import json
import re
import pandas

from bs4 import BeautifulSoup as bs


session = requests.Session()


def parseRaw(data: dict)->dict:
    # parsing 'nama' data
    soup = bs(data["nama"], "html.parser")
    element = soup.find("a")

    # split 'nama' into 'nama' and 'url'
    data["url"] = element["href"]
    data["nama"] = element.text

    # parsing 'lokasi' data
    lokasi = data["lokasi"]

    # remove number and <br> tag
    lokasi = re.sub(r'\d+|<br/>', '', lokasi)
    data["lokasi"] = lokasi

    return data

def getHtml(url: str)->str:
    response = session.get(url)
    print(f"{response.status_code}: {url}")

    return response.text

def parseText(text: str):
    result = dict()
    soup = bs(text, "html.parser")

    # detail tujuan
    dataTujuan = soup.find_all("div", class_="col-md-6")
    tujuanUmum = dataTujuan[0].p.text
    tujuanKhusus = dataTujuan[1].p.text

    # detail kegiatan
    def parseInfoKegiatan(soup, index):
        infoKegiatan = soup.find_all("p", class_="info-kegiatan text-center text-md-left")

        textToRemove = infoKegiatan[index].find_next().text

        getText = infoKegiatan[index].text.replace(textToRemove, "").strip()

        return getText
    
    periodeKegiatan = parseInfoKegiatan(soup, 1).split("(")[0]
    statusPelaksanaan = parseInfoKegiatan(soup, 2)

    # penanggungjawab
    penanggungjawab = parseInfoKegiatan(soup, 3)
    print(penanggungjawab)
    alamatPenanggungjawab = penanggungjawab.split(":")[1].strip()

    # lokasi
    try:
        lokasi = soup.find("li", class_="text-center text-md-left")
        lokasi = lokasi.text.replace("\r","").strip().split("\n")[0]
    except AttributeError:
        print("Lokasi tidak ditemukan")
        lokasi = "-"
    
    # recap data into dictionary result
    result["lokasi"] = lokasi
    result["tujuanUmum"] = tujuanUmum
    result["tujuanKhusus"] = tujuanKhusus
    result["periodeKegiatan"] = periodeKegiatan
    result["statusPelaksanaan"] = statusPelaksanaan
    result["alamatPenanggungjawab"] = alamatPenanggungjawab

    return result

def getData(jsonFile):
    finalResult = list()

    # load json file to get dictionary data
    rawData = json.load(open(jsonFile))["data"]

    baseUrl = "https://srn.menlhk.go.id"
    totalData = len(rawData)

    for i, data in enumerate(rawData):
        # extract raw data
        d = parseRaw(data)

        # container for temporary data
        temp = dict()

        # get additional data
        url = baseUrl + d["url"]

        try:
            text = getHtml(url)
            result = parseText(text)

        except IndexError:

            # catch error for server unable to retrieve data
            if "An internal server error occurred" in text:
                print("Internal server error")
            else:
                print("Data not found")

            # give dummy value
            result = {'lokasi': '-', 'tujuanUmum': '-', 'tujuanKhusus': '-', 'periodeKegiatan': '-', 'statusPelaksanaan': '-', 'alamatPenanggungjawab': '-'}

        # combine original data with additional data
        temp['ID'] = d['id']
        temp['Nama Kegiatan'] = d['nama']
        temp['Nama Penanggungjawab'] = d['nama_org']
        temp['Alamat Penanggungjawab'] = result['alamatPenanggungjawab']
        temp['No Registri'] = d['registrasi_number']
        temp['Periode Kegiatan'] = result['periodeKegiatan']
        temp['Durasi Kegiatan'] = d['durasi']
        temp['Status Pelaksanaan'] = result['statusPelaksanaan']
        temp['Lokasi'] = result['lokasi']
        temp['Tujuan Umum'] = result['tujuanUmum']
        temp['Tujuan Khusus'] = result['tujuanKhusus']

        finalResult.append(temp)
        print(f"Processed {i+1} of {totalData}")
    
    return finalResult


if __name__ == "__main__":
    filenames = ['raw100.json', 'raw200.json', 'raw288.json']

    # filenames = ['raw.json']

    # container for all data
    result = list()

    for file in filenames:
        temp = getData(file)
        result.extend(temp)
        print(f"getting {len(temp)} data from {file}")

    
    df = pandas.DataFrame(result)
    df.to_excel("data.xlsx", index=False)


    