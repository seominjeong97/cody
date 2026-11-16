"""색 조합 코디 공방
실행: streamlit run style_app.py
GitHub에 이 파일과 requirements.txt 업로드 → Streamlit Community Cloud에서 배포.
별도 데이터/로그인/AI/DB 설정 불필요. 카메라는 사진의 대표 색 추출용. QR 공유는 배포 주소를 QR로 변환하여 사용.
작업/컬렉션은 세션에만 보관되므로 종료/새로고침 전에 JSON 백업을 다운로드하세요.
JSON 가져오기로 복원 가능합니다. PNG는 도형 기반 스타일 보드이며 실제 착장/핏이 아닙니다.
"""
import colorsys
import copy
import io
import json
import random
import re
import uuid
import sqlite3
import secrets
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(page_title='색 조합 코디 공방',page_icon='🎨',layout='centered')
COLORS={'크림':'#F4EBDD','라벤더':'#B8A4CC','핑크':'#DCA7AF','민트':'#A6C4B5','하늘':'#9CBAD2','버터':'#E7CE83','네이비':'#344963','브라운':'#785849','차콜':'#434449','화이트':'#FAFAF7','진청':'#3D5773','코랄':'#D68673'}
ITEMS={'상의':['티셔츠','크롭 티셔츠','스트라이프 티','셔츠','블라우스','카라 티셔츠','니트','브이넥 니트','터틀넥','니트 베스트','민소매','맨투맨','후드','크롭 후드','집업 후드','카디건','데님 재킷','숏패딩','롱패딩','패딩 조끼'],'하의':['바지','청바지','슬랙스','와이드 팬츠','부츠컷 팬츠','조거 팬츠','카고 팬츠','린넨 팬츠','레깅스','반바지','데님 쇼츠','버뮤다 팬츠','스커트','미니 스커트','플리츠 스커트','롱 스커트','데님 스커트','머메이드 스커트'],'신발':['스니커즈','로퍼','부츠','샌들','플랫슈즈','하이힐','슬리퍼'],'가방':['숄더백','토트백','백팩','크로스백','클러치','버킷백']}
OUTER=['없음','카디건','집업 후드','데님 재킷','숏패딩','롱패딩','패딩 조끼']
ITEMS['상의']=[x for x in ITEMS['상의'] if x not in OUTER]
ITEMS['외투']=OUTER
MATERIALS=['기본','면','니트','데님','가죽','새틴','플리스']
PRESETS={'산뜻한 나들이':['#F4EBDD','#3D5773','#FAFAF7','#785849'],'라벤더 오후':['#B8A4CC','#F4EBDD','#434449','#DCA7AF'],'차분한 모노톤':['#FAFAF7','#434449','#434449','#9A9A9A'],'버터와 민트':['#E7CE83','#A6C4B5','#F4EBDD','#785849']}
PATTERNS=['무지','가로줄','세로줄','체크','도트','아가일']
MODES=['뉴트럴 + 포인트','톤온톤','유사색','보색 포인트','모노톤','자유 조합']

def default():
 return {'items':{k:ITEMS[k][0] for k in ITEMS},'colors':dict(zip(list(ITEMS)[:4],PRESETS['산뜻한 나들이']))|{'외투':'#B8A4CC'},'locks':{k:False for k in ITEMS},'background':'#F2F1EE'}
def valid_board(b):
 if not isinstance(b,dict): raise ValueError('보드 형식 오류')
 if b['items'].get('상의') in OUTER:
  b['items']['외투']=b['items']['상의'];b['items']['상의']='티셔츠'
  b['colors']['외투']=b['colors']['상의']
 b['items'].setdefault('외투','없음');b['colors'].setdefault('외투','#B8A4CC');b['locks'].setdefault('외투',False)
 for material in b.get('materials',{}).values():
  if material not in MATERIALS:raise ValueError('재질 설정 오류')
 for k in ITEMS:
  if b['items'][k] not in ITEMS[k] or not re.fullmatch(r'#[0-9a-fA-F]{6}',b['colors'][k]) or type(b['locks'][k]) is not bool: raise ValueError('아이템/색상 오류')
 if not re.fullmatch(r'#[0-9a-fA-F]{6}',b['background']): raise ValueError('배경 오류')
 for spec in b.get('patterns',{}).values():
  if spec.get('type') not in PATTERNS or not re.fullmatch(r'#[0-9a-fA-F]{6}',spec.get('color','')) or type(spec.get('size')) is not int or not 10<=spec['size']<=50:raise ValueError('무늬 설정 오류')
 return {key:{k:b[key][k] for k in ITEMS} for key in ['items','colors','locks']}|{'background':b['background'],'patterns':copy.deepcopy(b.get('patterns',{})),'materials':copy.deepcopy(b.get('materials',{}))}
def commit(board):
 valid_board(board)
 if board!=st.session_state.board:
  st.session_state.undo=(st.session_state.undo+[copy.deepcopy(st.session_state.board)])[-40:]
  st.session_state.redo=[];st.session_state.board=copy.deepcopy(board)
def rgb(hexcode): return tuple(int(hexcode[i:i+2],16) for i in (1,3,5))
def hexrgb(v): return '#'+''.join(f'{round(max(0,min(1,x))*255):02X}' for x in v)
def generate(board,mode):
 b=copy.deepcopy(board);h=random.random()
 for i,k in enumerate(ITEMS):
  if b['locks'][k]: continue
  if mode=='모노톤': color=hexrgb((lambda v:(v,v,v))(random.choice([.18,.4,.7,.94])))
  elif mode=='자유 조합': color=random.choice(list(COLORS.values()))
  elif mode=='뉴트럴 + 포인트': color=hexrgb(colorsys.hsv_to_rgb(h,.38,.82)) if i==3 else random.choice(['#F4EBDD','#434449','#785849','#FAFAF7'])
  elif mode=='보색 포인트': color=hexrgb(colorsys.hsv_to_rgb((h+(.5 if i==3 else 0))%1,.3 if i<3 else .6,random.uniform(.5,.92)))
  else: color=hexrgb(colorsys.hsv_to_rgb((h+(i*.045 if mode=='유사색' else 0))%1,random.uniform(.18,.45),random.uniform(.5,.95)))
  b['colors'][k]=color
 return b

def render_base(board):
 # 고해상도에서 그린 뒤 축소해 윤곽을 부드럽게 합니다.
 scale=3
 im=Image.new('RGB',(720*scale,800*scale),board['background']);d=ImageDraw.Draw(im)
 def tint(c,f):return tuple(min(255,max(0,round(v*f))) for v in rgb(c))
 def poly(points,fill,outline=None,w=1):
  pts=[(round(x*scale),round(y*scale)) for x,y in points];d.polygon(pts,fill=fill)
  if outline:d.line(pts+[pts[0]],fill=outline,width=max(1,round(w*scale)),joint='curve')
 def line(points,fill,w=1):d.line([(round(x*scale),round(y*scale)) for x,y in points],fill=fill,width=max(1,round(w*scale)),joint='curve')
 def box(rect,fill,r=0,outline=None,w=1):d.rounded_rectangle(tuple(round(v*scale) for v in rect),radius=round(r*scale),fill=fill,outline=outline,width=max(1,round(w*scale)))
 def oval(rect,fill,outline=None,w=1):d.ellipse(tuple(round(v*scale) for v in rect),fill=fill,outline=outline,width=max(1,round(w*scale)))
 # 쇼핑몰 플랫레이: 밝은 상품 카드와 낮은 대비의 바닥 그림자.
 for rect in [(65,30,436,333),(65,351,436,716),(459,90,681,405),(459,430,681,716)]:
  x,y,x2,y2=rect;box((x+3,y+6,x2+3,y2+6),'#E5DFDA',24);box(rect,'#FFFCF8',24)
 top=board['items']['상의'];c=board['colors']['상의'];edge=tint(c,.66);fold=tint(c,.85)
 cx=250;y=85;hem=285
 crop=top in ['크롭 티셔츠','크롭 후드'];hem=230 if crop else hem
 sleeveless=top in ['니트 베스트','민소매','패딩 조끼'];short=top in ['티셔츠','크롭 티셔츠','블라우스','카라 티셔츠']
 if sleeveless:
  pts=[(198,76),(224,68),(250,89),(276,68),(302,76),(292,137),(309,hem),(191,hem),(208,137)]
 elif short:
  pts=[(194,76),(224,68),(250,83),(276,68),(306,76),(353,139),(318,159),(300,133),(310,hem),(190,hem),(200,133),(182,159),(147,139)]
 else:
  pts=[(192,76),(224,68),(250,83),(276,68),(308,76),(355,235),(321,248),(294,149),(310,hem),(190,hem),(206,149),(179,248),(145,235)]
 poly(pts,c,edge,1.5)
 # 소매 봉제선과 밑단
 line([(195,84),(207,130)],fold);line([(305,84),(293,130)],fold)
 line([(195,hem-8),(305,hem-8)],fold,2)
 if top in ['브이넥 니트','니트 베스트','카디건']:
  poly([(224,70),(250,120),(276,70)],'#FFFCF8',edge,1.3)
 else:
  oval((224,66,276,101),'#FFFCF8',edge,1.5)
 if top in ['후드','크롭 후드','집업 후드']:
  oval((217,49,283,109),c,edge,1.5);oval((230,62,270,97),'#FFFCF8',edge)
  line([(237,104),(234,148)],edge,1.5);line([(263,104),(267,148)],edge,1.5)
  if top!='집업 후드':poly([(220,hem-66),(280,hem-66),(292,hem-23),(208,hem-23)],c,fold)
 if top in ['셔츠','블라우스','카라 티셔츠']:
  poly([(223,70),(249,97),(234,117),(212,83)],c,edge)
  poly([(277,70),(251,97),(266,117),(288,83)],c,edge)
 if top in ['셔츠','카디건','집업 후드','데님 재킷']:
  line([(250,105),(250,hem-5)],edge,1.3)
  for yy in range(130,hem-10,29):oval((248,yy,252,yy+4),'#D9BA82')
 if top in ['니트','브이넥 니트','니트 베스트','터틀넥']:
  for x in range(205,300,9):line([(x,145),(x,hem-13)],fold,.7)
 if top=='터틀넥':box((224,51,276,91),c,5,edge)
 if top=='맨투맨':
  box((224,147,276,178),tint(c,.92),5);line([(195,hem-15),(305,hem-15)],edge)
 if top=='스트라이프 티':
  for yy in range(120,hem-15,20):line([(205,yy),(295,yy)],edge,4)
 if top=='블라우스':
  line([(221,106),(250,126),(279,106)],edge);line([(250,126),(237,151)],edge);line([(250,126),(265,151)],edge)
 if top=='데님 재킷':
  for xx in [208,265]:box((xx,130,xx+28,166),c,2,edge);line([(xx,140),(xx+28,140)],fold)
 if top in ['숏패딩','롱패딩','패딩 조끼']:
  # 도톰한 몸판과 퀼팅을 같은 도형 소스에서 표현합니다.
  ph=310 if top=='롱패딩' else 266 if top=='숏패딩' else 280
  box((190,91,310,ph),c,15,edge,1.8)
  for yy in range(126,ph-12,29):
   line([(196,yy),(244,yy)],fold,2);line([(256,yy),(304,yy)],fold,2)
  box((220,65,280,105),tint(c,.9),10,edge)
  line([(250,91),(250,ph-5)],edge,3)
  for xx in [204,272]:
   box((xx,ph-65,xx+25,ph-25),tint(c,.96),5,edge)
   line([(xx+4,ph-60),(xx+21,ph-60)],edge,2)
  box((246,116,254,126),'#B7A795',2)
 # 하의 실루엣
 bottom=board['items']['하의'];c=board['colors']['하의'];edge=tint(c,.65);fold=tint(c,.83)
 skirt=bottom in ['스커트','미니 스커트','플리츠 스커트','롱 스커트','데님 스커트','머메이드 스커트']
 end=650 if bottom in ['롱 스커트','머메이드 스커트'] else 550 if skirt else 675
 if bottom=='미니 스커트':end=510
 if bottom in ['반바지','데님 쇼츠','버뮤다 팬츠']:end=520 if bottom!='버뮤다 팬츠' else 565
 if skirt:
  if bottom=='머메이드 스커트':pts=[(195,382),(305,382),(320,555),(362,end),(138,end),(180,555)]
  else:pts=[(193,382),(307,382),(340,end),(160,end)]
  poly(pts,c,edge,1.5)
  if bottom=='플리츠 스커트':
   for i in range(1,9):line([(193+i*12,398),(160+i*18,end-6)],fold,2)
  if bottom=='데님 스커트':line([(250,405),(250,end-8)],fold,2);line([(280,end-50),(280,end)],edge,1.5)
 else:
  wide=bottom in ['와이드 팬츠','린넨 팬츠','버뮤다 팬츠'];skinny=bottom=='레깅스';flare=bottom=='부츠컷 팬츠'
  outer=345 if wide or flare else 310 if not skinny else 290
  inner=262 if wide else 267 if flare else 275 if skinny else 268
  poly([(190,382),(310,382),(outer,end),(inner,end),(250,465),(500-inner,end),(500-outer,end)],c,edge,1.5)
  if bottom in ['슬랙스','와이드 팬츠','린넨 팬츠']:line([(216,425),(500-outer+18,end-12)],fold);line([(284,425),(outer-18,end-12)],fold)
  if bottom=='조거 팬츠':
   box((183,end-19,224,end),c,4,edge);box((276,end-19,317,end),c,4,edge)
  if bottom=='카고 팬츠':
   box((181,490,218,540),c,3,edge);box((282,490,319,540),c,3,edge)
 if bottom in ['청바지','데님 쇼츠','데님 스커트']:
  line([(195,405),(208,430),(230,433)],fold,2);line([(305,405),(292,430),(270,433)],fold,2)
  line([(250,405),(250,449)],fold,2)
 box((190,382,310,402),c,3,edge);oval((247,388,253,394),'#C9AC73')
 for x in [205,237,263,295]:line([(x,383),(x,400)],fold,2)
 # 가방: 종류별 구조를 따로 그립니다.
 bag=board['items']['가방'];c=board['colors']['가방'];edge=tint(c,.65);gold='#BDA477'
 if bag=='토트백':
  line([(520,205),(520,150),(539,133),(560,133),(579,150),(579,205)],edge,6)
  poly([(493,195),(620,195),(632,340),(481,340)],c,edge,1.7)
  line([(505,204),(500,330)],tint(c,1.1),2)
 elif bag=='숄더백':
  line([(503,236),(507,163),(530,142),(570,142),(602,167),(609,236)],edge,7)
  box((489,218,628,335),c,42,edge,1.7);line([(502,245),(615,245)],edge);box((548,237,570,254),gold,3)
 elif bag=='백팩':
  line([(536,162),(536,145),(573,145),(573,162)],edge,5)
  box((496,165,620,347),c,33,edge,1.7);box((510,261,606,327),tint(c,.94),13,edge)
  line([(511,233),(605,233)],edge,2);oval((597,228,601,240),gold)
 elif bag=='크로스백':
  line([(500,252),(512,135),(611,145),(619,252)],edge,5)
  box((491,244,625,340),c,18,edge,1.7);poly([(493,245),(624,245),(609,293),(507,293)],tint(c,.96),edge)
  box((548,280,568,299),gold,3)
 elif bag=='클러치':
  box((481,231,633,316),c,12,edge,1.7);poly([(484,234),(630,234),(557,280)],tint(c,1.04),edge)
  oval((551,274,563,286),gold)
 else:
  line([(514,211),(516,153),(540,136),(577,136),(604,155),(605,211)],edge,5)
  poly([(494,208),(620,208),(607,343),(508,343)],c,edge,1.7)
  line([(501,225),(614,225)],edge,2);line([(551,225),(541,282)],edge,2);line([(559,225),(570,283)],edge,2)
 # 신발: 스니커즈는 측면, 나머지는 위에서 본 한 쌍.
 shoe=board['items']['신발'];c=board['colors']['신발'];edge=tint(c,.6)
 if shoe=='스니커즈':
  for yy,dx in [(501,0),(591,12)]:
   poly([(483+dx,yy+28),(492+dx,yy),(535+dx,yy+5),(562+dx,yy+30),(620+dx,yy+42),(630+dx,yy+63),(479+dx,yy+63)],c,edge,1.7)
   box((478+dx,yy+58,632+dx,yy+70),'#F5EEDD',5,edge)
   for i in range(4):line([(526+dx+i*7,yy+19+i*4),(540+dx+i*7,yy+15+i*5)],'#FAF5ED',2.5)
   line([(500+dx,yy+34),(549+dx,yy+48)],tint(c,.8),3)
 else:
  for xx in [490,574]:
   if shoe=='부츠':
    box((xx,486,xx+48,607),c,6,edge,1.7);box((xx-3,578,xx+62,663),c,21,edge,1.7)
    line([(xx+9,490),(xx+9,583)],tint(c,1.15),2);box((xx-4,651,xx+64,666),edge,5)
   else:
    oval((xx,514,xx+57,662),c,edge,1.7)
    if shoe in ['로퍼','플랫슈즈','하이힐']:
     oval((xx+10,528,xx+47,600),'#E6D2BC',edge)
     if shoe=='로퍼':box((xx+2,587,xx+55,611),c,5,edge);line([(xx+17,600),(xx+40,600)],gold,3)
     elif shoe=='플랫슈즈':
      line([(xx+12,608),(xx+43,621),(xx+43,608),(xx+12,621),(xx+12,608)],edge,1.5)
     else:poly([(xx+4,640),(xx+53,640),(xx+28,681)],c,edge)
    else:
     oval((xx+7,520,xx+50,652),'#E6D2BC')
     box((xx+2,594,xx+55,618),c,6,edge)
     if shoe=='샌들':box((xx+3,542,xx+54,559),c,4,edge);line([(xx+8,551),(xx+8,606)],edge,3)
 for i,k in enumerate(ITEMS):
  x=244+i*64;oval((x,748,x+31,779),board['colors'][k],'#DDD2CA',1)
 return apply_patterns(apply_materials(im.resize((720,800),Image.Resampling.LANCZOS),board),board)

def apply_materials(image,board):
 regions={'상의':(137,45,364,320),'하의':(130,370,365,704),'신발':(473,480,651,704),'가방':(480,115,640,350)}
 for cat,material in board.get('materials',{}).items():
  if cat not in regions or material=='기본':continue
  base=rgb(board['colors'][cat]);pix=image.load();x0,y0,x1,y1=regions[cat]
  for y in range(y0,y1):
   for x in range(x0,x1):
    c=pix[x,y]
    if sum(abs(c[j]-base[j]) for j in range(3))>52:continue
    noise=((x*73+y*151+x*y*3)%23)-11
    delta=0
    if material=='면':delta=noise*.45
    elif material=='니트':delta=9 if x%7<2 else (-10 if (x+y//7)%7<2 else 0)
    elif material=='데님':delta=12 if (x+y)%6<2 else -7
    elif material=='가죽':delta=noise*.5+5*((x//19+y//13)%2)
    elif material=='새틴':delta=23*__import__('math').sin(x/26+y/68)
    elif material=='플리스':delta=noise*1.1+5*((x//3+y//3)%2)
    pix[x,y]=tuple(max(0,min(255,round(v+delta))) for v in c)
 return image

def render(board):
 valid_board(board)
 image=render_base(board)
 outer=board['items'].get('외투','없음')
 if outer!='없음':
  layer=copy.deepcopy(board);layer['items']['상의']=outer;layer['colors']['상의']=board['colors']['외투']
  layer['materials']=copy.deepcopy(board.get('materials',{}));layer['materials']['상의']=layer['materials'].get('외투','기본')
  layer['patterns']=copy.deepcopy(board.get('patterns',{}))
  if '외투' in layer['patterns']:layer['patterns']['상의']=layer['patterns']['외투']
  else:layer['patterns'].pop('상의',None)
  garment=render_base(layer)
  # 중앙을 열어 안쪽 상의도 보이게 겹칩니다.
  image.paste(garment.crop((137,45,235,320)),(137,45))
  image.paste(garment.crop((265,45,364,320)),(265,45))
 return image

def apply_patterns(image,board):
 # 원래 옷 색상 영역에만 무늬를 넣어 배경과 봉제선을 보존합니다.
 from PIL import ImageChops
 regions={'상의':(137,45,364,320),'하의':(130,370,365,704),'신발':(473,480,651,704),'가방':(480,115,640,350)}
 for category,spec in board.get('patterns',{}).items():
  if category not in regions or spec.get('type','무지')=='무지':continue
  rect=regions[category];tile=image.crop(rect);mask=Image.new('L',tile.size,0)
  base=rgb(board['colors'][category]);source=tile.load();mp=mask.load()
  for y in range(tile.height):
   for x in range(tile.width):
    if sum(abs(source[x,y][j]-base[j]) for j in range(3))<48:mp[x,y]=255
  ink=Image.new('RGBA',tile.size,(0,0,0,0));pen=ImageDraw.Draw(ink)
  step=spec['size'];color=spec['color'];kind=spec['type'];w,h=tile.size
  thickness=max(2,step//6)
  if kind in ['가로줄','체크']:
   for y in range(0,h,step):pen.rectangle((0,y,w,y+thickness),fill=color)
  if kind in ['세로줄','체크']:
   for x in range(0,w,step):pen.rectangle((x,0,x+thickness,h),fill=color)
  if kind in ['도트','아가일']:
   for row,y in enumerate(range(0,h+step,step)):
    for x in range(-(step//2),w+step,step):
     x+=step//2 if row%2 else 0
     r=max(2,step//6) if kind=='도트' else step//3
     if kind=='도트':pen.ellipse((x-r,y-r,x+r,y+r),fill=color)
     else:pen.polygon([(x,y-r),(x+r,y),(x,y+r),(x-r,y)],fill=color)
  alpha=ImageChops.multiply(ink.getchannel('A'),mask)
  tile.paste(ink,(0,0),alpha);image.paste(tile,rect[:2])
 return image

def png(board):
 b=io.BytesIO();render(board).save(b,format='PNG');return b.getvalue()

def mannequin(b):
 # 미리보기와 동일한 아이템을 합성하여 다른 디자인으로 바뀌지 않게 합니다.
 board=render(b)
 im=Image.new('RGB',(600,850),b['background']);d=ImageDraw.Draw(im)
 skin='#DED5CF'
 d.ellipse((267,18,333,105),fill=skin)
 d.rounded_rectangle((283,93,317,142),10,fill=skin)
 d.rounded_rectangle((238,135,362,422),24,fill=skin)
 for x in [245,316]:d.rounded_rectangle((x,399,x+39,743),16,fill=skin)
 d.line((300,782,300,821),fill='#B9ABA3',width=6)
 d.ellipse((237,814,363,831),fill='#D1C4BC')
 def piece(rect,size,pos):
  tile=board.crop(rect).convert('RGBA')
  pixels=tile.load()
  for y in range(tile.height):
   for x in range(tile.width):
    r,g,bl,al=pixels[x,y]
    if r>=252 and g>=249 and bl>=245:pixels[x,y]=(r,g,bl,0)
  tile=tile.resize(size,Image.Resampling.LANCZOS)
  im.paste(tile,pos,tile)
 piece((130,370,365,704),(180,348),(210,385))
 piece((473,480,651,704),(145,126),(229,698))
 piece((137,45,364,320),(272,285),(164,124))
 piece((480,115,640,350),(104,151),(392,341))
 return im

def persist():
 if 'workspace_id' not in st.session_state:return
 payload={k:st.session_state[k] for k in ['board','collection','compare']}
 with sqlite3.connect(str(Path(__file__).with_name('style_workspaces.sqlite'))) as db:
  db.execute('CREATE TABLE IF NOT EXISTS workspaces (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
  db.execute('INSERT OR REPLACE INTO workspaces VALUES (?,?)',(st.session_state.workspace_id,json.dumps(payload,ensure_ascii=False)))

def save_copy(name,tag):
 st.session_state.collection.append({'id':str(uuid.uuid4()),'name':name.strip() or '이름 없는 코디','tag':tag,'favorite':False,'board':copy.deepcopy(st.session_state.board)})

for k,v in {'board':default(),'undo':[],'redo':[],'collection':[],'compare':[],'revision':0}.items():
 if k not in st.session_state:st.session_state[k]=v
if 'workspace_id' not in st.session_state:
 token=st.query_params.get('workspace','')
 if not re.fullmatch(r'[0-9a-f]{48}',token):token=secrets.token_hex(24)
 st.session_state.workspace_id=token
 st.query_params['workspace']=token
 with sqlite3.connect(str(Path(__file__).with_name('style_workspaces.sqlite'))) as db:
  db.execute('CREATE TABLE IF NOT EXISTS workspaces (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
  row=db.execute('SELECT data FROM workspaces WHERE id=?',(token,)).fetchone()
 if row:
  try:
   data=json.loads(row[0]);valid_board(data['board'])
   st.session_state.board=data['board']
   for key in ['collection','compare']:st.session_state[key]=data.get(key,[])
  except (ValueError,KeyError,TypeError):st.warning('저장 자료를 불러오지 못했어요. 백업 파일을 사용해주세요.')

st.markdown('''<style>
#MainMenu,footer{display:none}
.st-key-show_mannequin button{min-height:42px!important;font-size:.95rem!important;border-radius:12px!important;font-weight:600!important}
.st-key-show_mannequin button p{font-size:.95rem!important;font-weight:600!important}
.st-key-show_flatlay button{min-height:42px!important}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"]{display:none!important}
.block-container{max-width:1120px;padding-top:4.5rem!important;padding-bottom:1.5rem}
[data-testid="stAppViewContainer"]{background:#FFF9F5;color:#49404A}
.brand-shell{background:linear-gradient(115deg,#FAE4EC,#EFE8FA 65%,#E7F2EC);border:1px solid #ECDCE6;border-radius:24px;padding:24px 28px;margin-bottom:16px}
.brand-shell h1{font-size:clamp(25px,4.5vw,36px)!important;line-height:1.5!important;padding:0!important;margin:0!important;overflow:visible!important;white-space:normal!important;word-break:keep-all;color:#574052}
.brand-shell p{margin:8px 0 0;color:#725F70;font-size:14px;line-height:1.7}
[data-testid="stHeadingWithActionElements"] a, [data-testid="stHeaderActionElements"], [data-testid="stHeadingActionElements"]{display:none!important}
h2,h3{font-size:1.2rem!important;line-height:1.6!important;padding-top:.35rem!important}
[data-testid="stVerticalBlock"]{gap:.65rem}
.stButton button,.stDownloadButton button{border-radius:16px;min-height:50px;padding:10px 14px;border:1px solid #E6D8E2;background:#FFFDFB;color:#594959;font-size:16px}
.stButton button:hover{background:#F6E4EE;border-color:#DCA6BC}
button[kind="primary"],button[kind="primaryFormSubmit"]{background:#BF3F58!important;color:white!important;border:0!important}
[data-testid="stFormSubmitButton"] button{min-height:38px!important;padding:6px 16px!important;width:auto!important}
[data-baseweb="select"]>div{border-radius:16px!important;background:#F7EFF5!important;border:1px solid #E6DAE6!important;min-height:46px}
[data-testid="stForm"]{border:1px solid #EADFE6;background:#FFFCFA;border-radius:20px;padding:16px}
[data-testid="stImage"]{background:#F3EEEB;border-radius:22px;overflow:hidden}
.shop-note{padding:14px 18px;background:#F2F5ED;border-radius:16px;color:#59654F;line-height:1.8;margin:12px 0}
.shop-label{font-size:13px;letter-spacing:2px;color:#9A6882;font-weight:700;margin:6px 0}
@media(max-width:767px){.block-container{padding:4rem 1rem 1rem!important}.brand-shell{padding:18px}.stButton button{width:100%;min-height:52px} [data-testid="stHorizontalBlock"]{gap:.5rem}}
</style>''',unsafe_allow_html=True)
# 로그인 없이 시작 버튼으로 입장하는 로고 화면입니다.
if not st.session_state.get('entered_studio',False):
 st.markdown('''<style>
 .welcome{max-width:650px;margin:1.5rem auto 1rem;text-align:center;padding:38px 24px 30px;border-radius:32px;background:linear-gradient(145deg,#FBE4EC,#F0E8FB 58%,#E7F3ED);border:1px solid #EBDCE7;box-shadow:0 14px 45px #B79BA51A}
 .welcome-logo{display:flex;justify-content:center;align-items:center;gap:14px;margin:0 auto 22px}
 .welcome-logo span{display:inline-flex;align-items:center;justify-content:center;width:72px;height:84px;border-radius:24px;background:#FFFCFA;font-size:40px;box-shadow:0 5px 12px #AC809516}
 .welcome-logo span:first-child{transform:rotate(-9deg)}.welcome-logo span:last-child{transform:rotate(9deg)}
 .welcome h1{font-size:clamp(27px,6vw,42px)!important;color:#664A60;line-height:1.5!important;margin:0!important;padding:0!important;word-break:keep-all}
 .welcome p{color:#786576;font-size:16px;line-height:1.9;margin:16px 0 8px;word-break:keep-all}
 .welcome-chips{margin-top:22px;display:flex;justify-content:center;gap:9px;flex-wrap:wrap}
 .welcome-chips span{background:#FFFCFAAA;border-radius:99px;padding:7px 13px;color:#80617B;font-size:13px}
 @media(max-width:767px){.welcome{margin-top:.3rem;padding:25px 14px}.welcome-logo span{width:58px;height:65px;font-size:31px}.welcome-logo{gap:10px}}
 </style>
 <div class="welcome">
 <div class="welcome-logo" aria-label="리본과 옷, 색상 팔레트"><span>🎀</span><span>👗</span><span>🎨</span></div>
 <h1>색 조합 코디 공방</h1>
 <p>오늘의 기분을 색으로 입어요.<br>좋아하는 색으로 만드는 나만의 작은 옷 가게</p>
 <div class="welcome-chips"><span>옷 그림으로 고르기</span><span>색 조합 꾸미기</span><span>나만의 코디 저장</span></div>
 </div>''',unsafe_allow_html=True)
 st.caption('로그인이나 사진 등록 없이 바로 시작할 수 있어요.')
 if st.button('나만의 코디 만들러 가기 →',type='primary',use_container_width=True,key='enter_studio'):
  st.session_state.entered_studio=True
  st.session_state.navigation='홈'
  persist();st.rerun()
 st.stop()

st.markdown('<div class="brand-shell"><h1>🎀 색 조합 코디 공방</h1><p>좋아하는 색으로 채우는 나만의 작은 옷 가게</p></div>',unsafe_allow_html=True)
if 'navigation' not in st.session_state:st.session_state.navigation='홈'
# 접는 사이드바 대신 항상 보이는 내비게이션. 좁은 화면은 3개씩 두 줄.
navs=[('홈','🏡 홈'),('작업실','🎨 작업실'),('비교실','🪞 비교실'),('컬렉션','🗂️ 컬렉션'),('카메라','📷 카메라'),('백업','📦 백업')]
for row in [navs[:3],navs[3:]]:
 for col,(value,label) in zip(st.columns(3),row):
  if col.button(label,key='nav_'+value,use_container_width=True,type='primary' if st.session_state.navigation==value else 'secondary'):
   st.session_state.navigation=value;persist();st.rerun()
page=st.session_state.navigation

def preset_change():
 new=default();new['colors']=dict(zip(list(ITEMS)[:4],PRESETS[st.session_state.preset]));commit(new);st.session_state.revision+=1

valid_board(st.session_state.board)
b=st.session_state.board
if page=='홈':
 st.markdown('<div class="shop-label">오늘의 코디 진열장</div>',unsafe_allow_html=True)
 st.write('오늘, 어떤 색이 끌리나요? 🌷')
 left,right=st.columns([1,1])
 with left:
  st.write('옷 사진이나 자료 없이 바로 시작하세요.')
  st.selectbox('준비된 스타일',list(PRESETS),key='preset',on_change=preset_change)
  st.caption('선택하면 오른쪽 코디에 바로 반영돼요.')
  st.markdown('<div class="shop-note">마음에 드는 스타일을 고르면 바로 미리 볼 수 있어요.<br>작업실에서 색을 바꾸고, 카메라로 일상의 색을 가져와 보세요.</div>',unsafe_allow_html=True)
  if st.button('이 코디 꾸미러 가기 →',use_container_width=True):
   st.session_state.navigation='작업실';persist();st.rerun()
  st.write(f'저장한 코디 **{len(st.session_state.collection)}개**')
 with right:st.image(render(st.session_state.board).resize((333,370)),use_container_width=True)
elif page=='작업실':
 left,right=st.columns([1,1.35])
 with left:
  if 'outfit_view' not in st.session_state:st.session_state.outfit_view='마네킹 착장'
  if st.button('👗 마네킹 보기',use_container_width=False,type='primary',key='show_mannequin'):
   st.session_state.outfit_view='마네킹 착장'
  if st.button('🧺 옷 펼쳐 보기',use_container_width=False,key='show_flatlay'):
   st.session_state.outfit_view='펼쳐 보기'
  st.image(mannequin(b) if st.session_state.outfit_view=='마네킹 착장' else render(b),use_container_width=True)
  a,c=st.columns(2)
  if a.button('비교에 추가'):
   if len(st.session_state.compare)<3:st.session_state.compare.append(copy.deepcopy(b));st.toast('비교실에 추가했어요.')
   else:st.toast('비교실에서 후보를 먼저 삭제해주세요.')
  if c.button('컬렉션에 저장'):
   save_copy('코디 '+str(len(st.session_state.collection)+1),'일상');st.toast('저장했어요.')
 with right:
  st.markdown('**그림을 보고 골라주세요 🎀**')
  if 'item_category' not in st.session_state:st.session_state.item_category='상의'
  for col,k in zip(st.columns(len(ITEMS)),ITEMS):
   if col.button(k,key='category_'+k,use_container_width=True,type='primary' if st.session_state.item_category==k else 'secondary'):
    st.session_state.item_category=k;persist();st.rerun()
  category=st.session_state.item_category
  color=st.color_picker(category+' 색상',b['colors'][category],key='color_'+category+'_'+str(st.session_state.revision))
  if color!=b['colors'][category]:
   new=copy.deepcopy(b);new['colors'][category]=color;commit(new);st.session_state.revision+=1;persist();st.rerun()
  material=b.get('materials',{}).get(category,'기본')
  st.write('🧵 재질')
  matcols=st.columns(4)
  for mi,mat in enumerate(MATERIALS):
   if matcols[mi%4].button(('✓ ' if mat==material else '')+mat,key='material_'+category+mat,use_container_width=True):
    new=copy.deepcopy(b);new.setdefault('materials',{})[category]=mat
    commit(new);st.session_state.revision+=1;persist();st.rerun()
  st.write('🎨 무늬 꾸미기')
  pattern_spec=b.get('patterns',{}).get(category,{'type':'무지','color':'#FAFAF7','size':24})
  with st.form('pattern_'+category+'_'+str(st.session_state.revision)):
   pc,cc=st.columns(2)
   pattern=pc.radio('무늬',PATTERNS,index=PATTERNS.index(pattern_spec['type']),horizontal=True)
   pattern_color=cc.color_picker('무늬 색',pattern_spec['color'])
   pattern_size=st.slider('무늬 간격 · 작게 ↔ 크게',10,50,pattern_spec['size'])
   if st.form_submit_button('무늬 적용',type='primary'):
    new=copy.deepcopy(b);new.setdefault('patterns',{})[category]={'type':pattern,'color':pattern_color,'size':pattern_size}
    commit(new);st.session_state.revision+=1;persist();st.rerun()
  st.caption('일러스트 아래의 이름 버튼을 누르면 바로 적용돼요. 접힌 목록은 없어요.')
  for offset in range(0,len(ITEMS[category]),3):
   for col,item in zip(st.columns(3),ITEMS[category][offset:offset+3]):
    with col:
     preview=copy.deepcopy(b);preview['items'][category]=item
     regions={'상의':(115,35,385,310),'하의':(125,365,370,700),'가방':(469,110,660,365),'신발':(469,475,665,700),'외투':(115,35,385,325)}
     picture=render(preview).crop(regions[category]);picture.thumbnail((190,175))
     tile=Image.new('RGB',(200,190),'#FFFCF8');tile.paste(picture,((200-picture.width)//2,(190-picture.height)//2))
     st.image(tile,use_container_width=True)
     selected=b['items'][category]==item
     if st.button(('✓ ' if selected else '')+item,key='pick_'+category+'_'+item,use_container_width=True,type='primary' if selected else 'secondary'):
      new=copy.deepcopy(b);new['items'][category]=item;commit(new);st.session_state.revision+=1;persist();st.rerun()
elif page=='비교실':
 if not st.session_state.compare:st.info('작업실에서 비교할 코디를 추가하세요.')
 else:
  for i,col in enumerate(st.columns(len(st.session_state.compare))):
   with col:
    st.image(render(st.session_state.compare[i]).resize((270,300)),caption=f'후보 {i+1}')
    if st.button('작업실로 불러오기',key='take'+str(i)):
     commit(st.session_state.compare[i]);st.session_state.revision+=1;st.toast('작업실에 반영했어요.')
    if st.button('후보 삭제',key='remove'+str(i)):st.session_state.compare.pop(i);persist();st.rerun()
elif page=='컬렉션':
 if not st.session_state.collection:st.info('작업실에서 코디를 저장해보세요.')
 else:
  names=[f'{i+1}. {x["name"]}' for i,x in enumerate(st.session_state.collection)]
  index=st.selectbox('저장한 코디',range(len(names)),format_func=lambda i:names[i]);x=st.session_state.collection[index]
  a,c=st.columns(2)
  with a:st.image(render(x['board']).resize((315,350)),width=315)
  with c:
   name=st.text_input('이름',x['name'],max_chars=80,key='name'+x['id'])
   if st.button('이름 변경'):x['name']=name.strip() or '나의 코디';persist();st.rerun()
   if st.button('작업실로 불러오기'):
    commit(x['board']);st.session_state.revision+=1;st.toast('작업실에 반영했어요.')
   st.download_button('코디 이미지 받기',png(x['board']),'style_board.png','image/png')
   confirm=st.checkbox('이 코디 삭제 확인')
   if st.button('삭제',disabled=not confirm):st.session_state.collection.pop(index);persist();st.rerun()
elif page=='카메라':
 st.write('📷 사진에서 마음에 드는 색 가져오기')
 st.caption('가상 피팅이 아닌 색 추출 기능이에요. 카메라 허용이 필요하며 사진은 장기 저장하지 않아요.')
 a,c=st.columns(2)
 with a:
  source=st.radio('사진 선택 방법',['카메라 촬영','사진 업로드'],horizontal=True)
  photo=st.camera_input('사진 촬영') if source=='카메라 촬영' else st.file_uploader('사진 선택',type=['jpg','jpeg','png','webp'])
 with c:
  if photo:
   try:
    if photo.size>12000000:raise ValueError('12MB 이하 사진을 사용해주세요.')
    image=Image.open(photo)
    if image.width*image.height>25000000:raise ValueError('사진 해상도가 너무 커요. 축소해서 올려주세요.')
    from PIL import ImageOps
    image=ImageOps.exif_transpose(image).convert('RGB');image.thumbnail((400,400))
    quant=image.quantize(colors=6);palette=quant.getpalette();counts=sorted(quant.getcolors(),reverse=True)
    shades=['#'+''.join(f'{n:02X}' for n in palette[i*3:i*3+3]) for count,i in counts]
    st.image(image,width=230)
    color=st.selectbox('추출한 대표 색',shades)
    st.color_picker('선택한 색 미리보기',color,disabled=True)
    target=st.selectbox('적용할 아이템',list(ITEMS))
    if st.button('이 색 적용',type='primary'):
     new=copy.deepcopy(b);new['colors'][target]=color;commit(new);st.session_state.revision+=1;st.success('작업실에 반영했어요.')
   except Exception:st.error('사진을 읽지 못했어요. 12MB 이하 일반 사진으로 다시 시도해주세요.')
  else:st.info('옷이나 사물의 사진을 찍으면 대표 색 6개를 찾아드려요. 배경 색도 포함될 수 있어요.')
else:
 st.write('작업 백업과 복원')
 st.warning('새로고침·세션 종료 시 작업이 사라질 수 있어요. JSON 파일로 보관하세요.')
 backup={'schema':1,'board':b,'collection':st.session_state.collection}
 st.download_button('전체 작업 백업',json.dumps(backup,ensure_ascii=False,indent=2).encode(),'style_backup.json','application/json')
 uploaded=st.file_uploader('백업 파일 선택',type=['json'])
 confirm=st.checkbox('현재 작업과 컬렉션을 백업 내용으로 교체합니다.')
 if st.button('백업 복원',disabled=uploaded is None or not confirm):
  try:
   if uploaded.size>2000000:raise ValueError()
   data=json.loads(uploaded.getvalue())
   if data.get('schema')!=1 or not isinstance(data['collection'],list) or len(data['collection'])>500:raise ValueError()
   board=valid_board(data['board']);clean=[]
   for x in data['collection']:
    if not isinstance(x['name'],str) or len(x['name'])>80:raise ValueError()
    clean.append({'id':str(uuid.uuid4()),'name':x['name'],'tag':'일상','favorite':False,'board':valid_board(x['board'])})
   st.session_state.board=board;st.session_state.collection=clean;st.session_state.compare=[];st.session_state.undo=[];st.session_state.redo=[];st.session_state.revision+=1;st.success('복원했어요.')
  except Exception:st.error('유효한 앱 백업 파일을 선택해주세요. 기존 작업은 유지돼요.')
 st.caption('화면 속 색과 실제 원단의 색은 다를 수 있어요. 사진의 대표 색 추출은 퍼스널컬러 분석이나 착장 합성이 아닙니다.')

persist()
st.caption('자동 저장됨 · 이 페이지 주소를 북마크해야 다음에 내 착장이 복원돼요. 개인 작업 주소를 공유하지 마세요. 서버 재배포 시 저장이 사라질 수 있으니 백업도 받아주세요.')
