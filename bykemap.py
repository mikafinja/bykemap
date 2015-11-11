#!/bin/python3

# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw, ImageFilter
from lxml import etree
import math
import sys
import urllib.request
import PIL.ImageOps
import colorsys
import os



class bykemap():
	def __init__(self):
		self.coords = []
		self.minLat = None
		self.maxLat = None
		self.minLon = None
		self.maxLon = None
		self.mercator = []
		self.minMerLat = None
		self.maxMerLat = None
		self.minMerLon = None
		self.maxMecLon = None
		self.points = []
		self.tilesX = []
		self.tilesY = []
		self.zoom = 14
		self.zoomDist = {9: 150, 10: 152, 11:40, 12: 25, 13: 19.1, 14: 9.558, 15: 3, 16: 1.5, 17: 0.9}

	def setZoom(self, zoom):
		if zoom in self.zoomDist:
			self.zoom = int(zoom)
		else:
			print("Zoom not in valid range from 9 to 17")
			sys.exit(1)

	def addGpx(self, gpxFile):
		os.system("gpsbabel -i gpx -f " + gpxFile + " -x position,distance=" + str(self.zoomDist[self.zoom])  + "m -o gpx -F /tmp/bykemap.gpx")
		with open("/tmp/bykemap.gpx") as gpx:
			tree = etree.parse(gpx)
		root = tree.getroot()
		nspace = root.tag[:-3]
		for element in root.iter(nspace+"trkpt"):
			self.coords.append({'lat': float(element.attrib['lat']), 'lon': float(element.attrib['lon'])})

	def transformMercator(self):
		for coord in self.coords:
			lat = math.pi * coord['lat'] / 180
			lon = math.pi * coord['lon'] / 180
			self.mercator.append({
				'lon': lon,
				'lat': math.log(math.tan(math.pi/4 + lat/2))
			})
		self.minMerLon = math.pi * self.minLon / 180
		self.maxMerLon = math.pi * self.maxLon / 180
		self.minMerLat = math.pi * self.minLat / 180
		self.maxMerLat = math.pi * self.maxLat / 180
		self.minMerLat = math.log(math.tan(math.pi/4 + self.minMerLat/2))
		self.maxMerLat = math.log(math.tan(math.pi/4 + self.maxMerLat/2))

	def getMinmaxCoords(self):
		for coord in self.coords:
			if self.minLat == None:
				self.minLat = coord['lat']
				self.maxLat = coord['lat']
				self.minLon = coord['lon']
				self.maxLon = coord['lon']
			else:
				self.minLat = min(self.minLat, coord['lat'])
				self.maxLat = max(self.maxLat, coord['lat'])
				self.minLon = min(self.minLon, coord['lon'])
				self.maxLon = max(self.maxLon, coord['lon'])

	def getPoints(self):
		for mer in self.mercator:
			x = ((mer['lon']-self.minMerLon)/(self.maxMerLon-self.minMerLon))
			y = (1-(mer['lat']-self.minMerLat)/(self.maxMerLat-self.minMerLat))
			self.points.append((x,y))

	def getTiles(self):
		n = 2.0 ** self.zoom
		lat_rad = math.radians(self.maxLat)
		ulxtile = int((self.minLon + 180.0) / 360.0 * n)
		ulytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
		lat_rad = math.radians(self.minLat)
		lrxtile = int((self.maxLon + 180.0) / 360.0 * n)
		lrytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
		self.tilesX = list(range(ulxtile, lrxtile+1))
		self.tilesY = list(range(ulytile, lrytile+1))

	def getDimension(self):

		n = 2.0 ** self.zoom
		lon_deg = (self.tilesX[0]) / n * 360.0 - 180.0
		lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * (self.tilesY[0]) / n)))
		lat_deg = math.degrees(lat_rad)
		self.maxLat = lat_deg
		self.minLon = lon_deg
		lon_deg = (self.tilesX[-1]+1) / n * 360.0 - 180.0
		lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * (self.tilesY[-1]+1) / n)))
		lat_deg = math.degrees(lat_rad)
		self.minLat = lat_deg
		self.maxLon = lon_deg

	def plotTracks(self):
		width = 256 * len(self.tilesX)
		height = 256 * len(self.tilesY)
		points = map(lambda x : (x[0]*width, x[1]*height), self.points)
		im0 = Image.new('RGBA', (width, height), (255, 255, 255, 0))
		draw0 = ImageDraw.Draw(im0)

		for point in points:
			draw0 = ImageDraw.Draw(im0)
			#draw0.ellipse((point[0]-1,point[1]-1,point[0]+1,point[1]+1,), outline=(0,255,0,64))
			draw0.point((point[0],point[1]), fill=(0,255,0,128))

		im0.save("point.png", "PNG")

	def plotTracks2(self):
		width = 256 * len(self.tilesX)
		height = 256 * len(self.tilesY)
		points = map(lambda x : (x[0]*width, x[1]*height), self.points)
		img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
		draw = ImageDraw.Draw(img)
		pixels = {}
		for point in points:
			pixel = (int(point[0]), int(point[1]))
			if pixel in pixels:
				pixels[pixel] += 1
			else:
				pixels[pixel] = 1

		print(pixels)
		minval = (min(pixels.values()))
		print(minval)

		maxval = (max(pixels.values()))
		print(maxval)

		for pixel, count in pixels.items():
			h_val = ((1/2)/(maxval))*(count-1)
			print(h_val)
			#rgb_val = colorsys.hsv_to_rgb(h_val, 0.8+0.2/count ,1)
			rgb_val = colorsys.hsv_to_rgb(h_val, 1 ,1)
			color = (int(rgb_val[0]*256),int(rgb_val[1]*256),int(rgb_val[2]*256),256)
			print (pixel, color, count)
			if (self.zoom <= 11):
				draw.point((pixel[0],pixel[1]), fill=color)
			else:
				draw.ellipse((pixel[0]-1,pixel[1]-1,pixel[0]+1,pixel[1]+1,), outline=color, fill=color)
		img.save("point.png", "PNG")


	def downloadTiles(self):
		imgMap = Image.new('RGB', (256*len(self.tilesX), 256* len(self.tilesY)), (255,255,255))
		for x in self.tilesX:
			for y in self.tilesY:
				url = ("http://b.tile.stamen.com/toner-lite/%s/%s/%s.png" % (self.zoom, x,y))
				#url = ("http://a.basemaps.cartocdn.com/dark_all/%s/%s/%s.png" % (self.zoom, x, y))
				print(url)
				urllib.request.urlretrieve(url, "/tmp/tile.png")
				tile = Image.open("/tmp/tile.png")
				imgMap.paste(tile, (256*self.tilesX.index(x), 256*self.tilesY.index(y)))
		imgMap = PIL.ImageOps.invert(imgMap)
		#imgMap.paste(im0, mask=im0)
		imgMap.save("dlmap.png", "PNG")

		bg = Image.open("dlmap.png")
		point = Image.open("point.png")

		bg.paste(point, mask=point)
		bg.save("output.png")

foo = bykemap()
foo.setZoom(14)
for f in sys.argv[1:]:
	foo.addGpx(f)
foo.getMinmaxCoords()
foo.getTiles()
foo.getDimension()
foo.transformMercator()
foo.getPoints()
foo.plotTracks2()
foo.downloadTiles()

sys.exit(0)
