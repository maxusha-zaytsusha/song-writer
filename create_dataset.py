import requests
from bs4 import BeautifulSoup
import pandas as pd
import json


def create_dataset(bands: list, headers: dict) -> pd.DataFrame:
	'''
	bands - список названий групп
	headers - заголовки для запроса с заголовками Accept и User-Agent:
		
	Возвращает pandas.DataFrame с текстами песен.
	Датафрейм содержит следующие колонки:
		band - название группы
		song - название песни
		lyrics - текст песни
	'''

	# датасет, который будет преобразован в pandas.DataFrame 
	res = []

	# функция для предобработки текста
	# удаляет текст в скобках, в них почти всегда указываюься авторы, либо помечаются куплеты и припевы
	# удаляет пробел после начала новой строки
	# удаляет переносы строк в начале текста
	def processing(s):

		i = 0
		j = 0

		while i < len(s):

			if s[i] in ("[", "("):
				j = i

			elif s[i] in ("]", ")"):
				s = s[:j] + s[i+1:]
				i = j

			i += 1

		s = s.replace("\n ", "\n")

		while s and s[0] == "\n":
			s = s[1:]

		return s

	# цыкл мо группам
	for band in bands:

		print("loading", band, "band")
		
		# запрашиваем страницу со списком песен группы
		href = "https://www.elyrics.net/song/" + band[0] + "/" + band.replace(" ", "-") + "-lyrics.html"
		req = requests.get(href, headers)
		soup = BeautifulSoup(req.text, 'html.parser')

		# заполняем массив с песнями группы и ссылками на их тексты
		songs = []
		for song in soup.find_all("a", class_= "pl-0"):
			songs.append({
				"name": song.text[1:],
				"href": song["href"]
			})

		# цыкл по песням группы
		for song in songs:

			# запрашиваем страницу с текстом песни
			req = requests.get("https://www.elyrics.net" + song["href"], headers)
			soup = BeautifulSoup(req.text, 'html.parser')

			# читаем текст песни
			text = processing(soup.find("div", id="inlyr").text.replace("\n\n", "\n"))

			# если в песне есть текст (иначе в text будет написано 'instrumental' или 'no lyrics')
			if len(text) > 100:
				# добавляем песню в датасет
				res.append({
					"band": band,
					"song": song["name"],
					"lyrics": text
				})
	
	# возвращаем датасет в виде pandas.DataFrame и удаляем песни с одиноковым названием, так как это скорее всего каверы
	return pd.DataFrame(res).drop_duplicates(subset='song', keep='first')

if __name__ == "__main__":

	# задаем заголовки
	st_accept = "text/html"
	st_useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 YaBrowser/	24.10.0.0 Safari/537.36"
	
	headers = {
	   "Accept": st_accept,
	   "User-Agent": st_useragent
	}

	# читаем json с названиями групп, тектсы которых хотим загрузить
	with open("bands.json", "r") as f:
		bands = json.load(f)

	# создаем датасет 
	df = create_dataset(bands, headers)

	# сохраняем его в csv файл
	df.to_csv("dataset.csv", index=False)

	print("dataset loading complete!")