from filewrappers import PSXRAMFileDescriptor as psxram
from struct import unpack
from json import load
from tkinter import *
from PIL import Image
from PIL.ImageTk import PhotoImage
from idlelib.tooltip import Hovertip


with open("carddata/monsters.txt", "r") as file:
    MONSTERS = [x.replace("\n", "").split(":") for x in file.readlines()]
    for x in range(len(MONSTERS)):
        if MONSTERS[x][2] == "":
            MONSTERS[x][2] = 0
        else:
            MONSTERS[x][2] = int(MONSTERS[x][2])


with open("carddata/general.json", "r") as file:
    general = load(file)


with open("carddata/specific.json", "r") as file:
    specific = load(file)


with open("carddata/card_type.json", "r") as file:
    types = load(file)


def minatk(card1, card2, card3):
    return MONSTERS[card1][2] < MONSTERS[card3][2] or MONSTERS[card1][2] < MONSTERS[card3][2]


def pick(card1, card2, candidates):
    for x in candidates:
        if MONSTERS[card1][2] >= MONSTERS[x][2] or MONSTERS[card2][2] >= MONSTERS[x][2]:
            candidates.remove(x)
    if len(candidates) == 0:
        return None
    return candidates[0]


def search(name):
    name = name.lower().replace(" ", "").replace("-", "")
    candidates = []
    for x in range(len(MONSTERS)):
        if name == MONSTERS[x][0].lower().replace(" ", "").replace("-", ""):
            return [x]
        if name in MONSTERS[x][0].lower().replace(" ", "").replace("-", ""):
            candidates.append(x)
    return candidates


def check(card1, card2):
    candidates = []
    
    for x in general:
        if card1 in (x[0] if isinstance(x[0], list) else types[x[0]]) and \
            card2 in (x[1] if isinstance(x[1], list) else types[x[1]]):
            candidates.append(x[2])
    
    if str(card1) in specific.keys():
        if str(card2) in specific[str(card1)].values():
            candidates.append(specific[str(card1)][str(card2)])
    
    return candidates


class Hand():
    def __init__(self, base_address):
        self.ram = psxram("Yu-Gi-Oh! Forbidden Memories", int(base_address, 16))
    
    @property
    def cards(self):
        hand = []

        self.ram.seek(0x1a7ae4)
        for x in range(5):
            card = unpack("H26x", self.ram.read(0x1c))[0]
            hand.append(card)

        return [x - 1 for x in hand]
    
    def check(self):
        fusions = []
        
        cards = self.cards
        cardn = len(cards)
        
        for x, y in [(y, x) for y in range(cardn) for x in range(cardn) if x != y]:
            cands = check(cards[x], cards[y])
            fusion = pick(cards[x], cards[y], cands)
            if fusion is not None:
                fusions.append((cards[x], cards[y], fusion))
        
        # clean
        clean = set()
        for x in fusions:
            clean.add(tuple(sorted(x[:2])+[x[-1]]))
        
        return list(clean)
    
    def deepcheck(self):
        prevfusions = self.check()
        cards = self.cards
        fusions = prevfusions.copy()
        
        for mat in prevfusions:
            for card in cards:
                if card not in mat[:2] or cards.count(card) > 1:
                    cands = check(mat[2], card)
                    fusion = pick(mat[2], card, cands)
                    if fusion is not None and fusion not in [x[2] for x in prevfusions] and minatk(mat[2], card, fusion):
                        print(minatk(mat[2], card, fusion))
                        fusions.append((mat[2], card, fusion))
                    # check the other way around
                    cands = check(card, mat[2])
                    fusion = pick(card, mat[2], cands)
                    if fusion is not None and fusion not in [x[2] for x in prevfusions] and minatk(mat[2], card, fusion):
                        fusions.append((mat[2], card, fusion))
        
        clean = set()
        for x in fusions:
            clean.add(tuple(sorted(x[:2])+[x[-1]]))
        
        return list(clean)
    
    def draw(self):
        while True:
            name = input("Card name: ")
            card = search(name)
            if len(card) == 0:
                print("Card not found.")
                continue
            if len(card) > 1:
                print(f'{len(card)} matches for {name}')
                for x in card:
                    print(f'\t{MONSTERS[x][0]}')
                continue
            self.cards.extend(card)
            break
    
    def multidraw(self, cards):
        for x in range(int(cards)):
            self.draw()


def load_img(id):
    return PhotoImage(Image.open(f'cards/{id:0>3}.jpg').resize((75, 100)))


class App(Tk):
    def __init__(self):
        super().__init__()
        self.title("YGO FM Fusion Finder")
        self.geometry("249x1007")
        
        self.base_address = StringVar()
        self.fusions = []
        
        self.BACK = PhotoImage(Image.open(f'cards/back.jpg').resize((75, 100)))
        
        self.baframe = Frame(self)
        Label(self.baframe, text="Base address: ").pack()
        Entry(self.baframe, textvariable=self.base_address).pack()
        Button(self.baframe, text="Ok", command=self.setHand).pack()
        
        self.baframe.pack()
        
        self.fusionframe = Frame(self)
        self.offset = 0
        self.first = []
        self.second = []
        self.result = []
        self.tooltips = []
        for x in range(9):
            self.first.append(Label(self.fusionframe, image=self.BACK, borderwidth=4, relief="ridge"))
            self.first[-1].grid(column=0, row=x+2)
            
            self.second.append(Label(self.fusionframe, image=self.BACK, borderwidth=4, relief="ridge"))
            self.second[-1].grid(column=1, row=x+2)
            
            self.result.append(Label(self.fusionframe, image=self.BACK, borderwidth=4, relief="ridge"))
            self.result[-1].grid(column=2, row=x+2)
            self.tooltips.append(Hovertip(self.result[-1],'Huh'))
        
        self.clear()
        
        self.controlframe = Frame(self.fusionframe)
        self.controlframe.grid(columnspan=3, column=0, row=0)
        
        self.checkbutton = Button(self.controlframe, text="Check Fusions", command=self.check)
        self.checkbutton.grid(column=1, row=0)
        
        self.downbutton = Button(self.controlframe, text="v", command=self.down)
        self.downbutton.grid(column=2, row=0)
        
        self.upbutton = Button(self.controlframe, text="^", command=self.up)
        self.upbutton.grid(column=0, row=0)
        
    
    def up(self):
        self.offset = max(0, self.offset - 1)
        self.drawFusions()
        
    def down(self):
        self.offset += 1
        self.drawFusions()
    
    def check(self):
        self.offset = 0

        #fusions = self.hand.check()
        self.fusions = self.hand.deepcheck()
        
        self.drawFusions()
        
    def drawFusions(self):
        self.fusions = sorted(self.fusions, key=lambda x: MONSTERS[x[2]][2], reverse=True)
        
        self.clear()
        for x in range(min(9, len(self.fusions)-self.offset)):
            self.first[x].img = load_img(self.fusions[x+self.offset][0])
            self.first[x].configure(image=self.first[x].img)
            
            self.second[x].img = load_img(self.fusions[x+self.offset][1])
            self.second[x].configure(image=self.second[x].img)
            
            self.result[x].img = load_img(self.fusions[x+self.offset][2])
            self.result[x].configure(image=self.result[x].img)
            self.tooltips[x].text = str(MONSTERS[self.fusions[x][2]][2])
    
    def clear(self):
        for x in range(9):
            self.first[x].configure(image=self.BACK)
            self.second[x].configure(image=self.BACK)
            self.result[x].configure(image=self.BACK)
            self.tooltips[x].text = ""
    
    def setHand(self):
        self.baframe.pack_forget()
        self.hand = Hand(self.base_address.get())
        self.fusionframe.pack()
    
    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()