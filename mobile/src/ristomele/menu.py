from ristomele import model

Item = model.MenuItem
Drink = lambda name, price: model.MenuItem(name=name, price=price, is_drink=True)
Foc = lambda name, price: model.MenuItem(name='Foc. '+ name, price=price)
Sep = lambda name: model.MenuItem(kind='separator', name=name)

def get_menu():
    #return menu_13_agosto()
    #return menu_14_agosto()
    return menu_sagra()

def menu_sagra():
    return [
        Sep('Focaccini'),
        Foc('Zeneize de Me', 2),
        Foc('Boscaiolo e cotto', 5.5),
        Foc('Boscaiolo e crudo', 5.5),
        Foc('Boscaiolo e speck', 5.5),
        Foc('Brie e miele', 4),
        Foc('Cotto', 4),
        Foc('Cotto e pistacchio', 5),
        Foc('Cotto e stracchino', 5),
        Foc('Cotto, stracchino e pistacchio', 6),
        Foc('Crema di carciofi', 4),
        Foc('Crema di carciofi e cotto', 5),
        Foc('Crema di carciofi e crudo', 5),
        Foc('Crema di carciofi e salame', 5),
        Foc('Crema di carciofi e salame piccante', 5),
        Foc('Crema di carciofi e speck', 5),
        Foc('Crudo', 4),
        Foc('Crudo e pistacchio', 5),
        Foc('Crudo e stracchino', 5),
        Foc('Crudo, stracchino e pistacchio', 6),
        Foc('Gorgonzola', 4),
        Foc('Gorgonzola e noci', 5),
        Foc('Gorgonzola e pistacchio', 5),
        Foc('Gorgonzola, miele e noci', 5),
        Foc('Pesto', 4),
        Foc('Pesto e stracchino', 5),
        Foc('Porchetta', 5),
        Foc('Porchetta e cipolle', 5.5),
        Foc('Porchetta e pistacchio', 6),
        Foc('Salame', 4),
        Foc('Salame piccante', 4),
        Foc('Salame piccante e gorgo', 5),
        Foc('Salame picc. e stracchino', 5),
        Foc('Salsiccia', 5),
        Foc('Salsiccia e cipolle', 5.5),
        Foc('Speck', 4),
        Foc('Speck e brie', 5),
        Foc('Speck e pistacchio', 5),
        Foc('Speck, brie e pistacchio', 6),
        Foc('Stracchino', 4),
        Foc('Stracchino e pistacchio', 5),
        Foc('Crema al Pistacchio', 5),
        Foc('Nutella', 4),

        Sep('Focaccini Speciali del Giorno'),
        Foc('VENERDI - Pancetta affumicata e peperoni grigliati', 6.5),
        Foc('SABATO - Mortadella, salsa al pistacchio e burratina', 6.5),
        Foc('DOMENICA - Fesa di tacchino e salsa tonnata', 6.5),

        Sep('Alla piastra'),
        Item(name='Salsiccia', price=4.5),
        Item(name='Salsiccia e patatine', price=5.5),
        Item(name='Porchetta', price=4.5),
        Item(name='Porchetta e patatine', price=5.5),
        Item(name='Patate fritte', price=3),

        Sep('BAR'),
        Drink('ECO-Bicchiere', 1),
        Drink('Bicchiere Piccolo Vino', 1.5),
        Drink('Bicchiere Grande Vino', 3),
        Drink('Birra artigianale PILS', 5),
        Drink('Birra artigianale WEISS', 5),
        Drink('Sangria', 5),
        Drink('Spritz', 5),
        Drink('Acqua minerale 0.50L', 1),
        Drink('Coca Cola', 2),
        Drink('Fanta', 2),
        Drink('Gazzosa', 2),
        Drink('THE Limone', 2),
        Drink('THE Pesca', 2),
        Drink('Amaro Camatti', 3),
        Drink('Liquore Liquirizzia', 3),
        Drink('Caffe', 1),
    ]



def menu_13_agosto():
    """
    13 agosto, fugassin
    """
    return [
        Sep(name='Focaccini'),
        Foc(name='Zeneize de Me', price=2),
        Foc(name='Zeneize + zucchero ', price=2),
        Foc(name='Boscaiolo + cotto', price=5.5),
        Foc(name='Boscaiolo + crudo', price=5.5),
        Foc(name='Cotto', price=4),
        Foc(name='Cotto + pistacchio', price=5),
        Foc(name='Cotto + stracchino', price=5),
        Foc(name='Cotto + stracch + pist', price=6),

        Foc(name='Carciofi', price=4),
        Foc(name='Carciofi + cotto', price=5),
        Foc(name='Carciofi + crudo', price=5),
        Foc(name='Carciofi + salame', price=5),

        Foc(name='Crudo', price=4),
        Foc(name='Crudo + pistacchio', price=5),
        Foc(name='Crudo + stracchino', price=5),
        Foc(name='Crudo + stra + pist', price=6),

        Foc(name='Porchetta', price=5),
        Foc(name='Porchetta + pistacchio', price=6),
        Foc(name='Salame', price=4),
        Foc(name='Salsiccia', price=5),
        Foc(name='Stracchino', price=4),
        Foc(name='Stracchino + pistacchio', price=5),
        Foc(name='Pistacchio dolce', price=4),
        Foc(name='Nutella', price=4),

        Sep(name='Alla piastra'),
        Item(name='Salsiccia', price=4),
        Item(name='Salsiccia + patatine', price=5),
        Item(name='Porchetta', price=4),
        Item(name='Porchetta + patatine', price=5),
        Item(name='Patatine fritte', price=3),

        Sep(name='Vino'),
        Drink(name='Bicchiere piccolo rosso ', price=1.5),
        Drink(name='Bicchiere piccolo bianco ', price=1.5),
        Drink(name='Bicchiere grande rosso ', price=3),
        Drink(name='Bicchiere grande bianco ', price=3),
        Drink(name='Sangria', price=5),

        Sep(name='Altre bevande'),
        Drink(name='Birra PILS', price=5),
        Drink(name='Birra WEISS', price=5),
        Drink(name='Coca Cola', price=2),
        Drink(name='Aranciata', price=2),
        Drink(name='Gazzosa', price=2),
        Drink(name='The Limone', price=2),
        Drink(name='The Pesca', price=2),

        Drink(name='Acqua naturale 0.5L', price=1),
        Drink(name='Acqua frizzante 0.5L', price=1),
        ## Drink(name='Bicchiere Spuma', price=0.5),
        ## Drink(name='Bottiglia Spuma', price=3),
        Drink(name='Amaro camatti', price=3),
        Drink(name='Liquore liquirizia', price=3),
        Drink(name='Caffe', price=1),
    ]

def menu_14_agosto():
    """
    14/15 agosto, ristorante
    """
    return [
        Item(name='Coperto', price=1.5),
        Sep(name='Primi'),
        Item(name='Ravioli au Tuccu', price=8),
        Item(name='Trenette al pesto', price=6.5),

        Sep(name='Secondi'),
        Item(name='Salsiccia', price=4),
        Item(name='Salsiccia + patatine', price=5),
        Item(name='Salsiccia + pomodori', price=5),

        Item(name='Porchetta', price=4),
        Item(name='Porchetta + patatine', price=5),
        Item(name='Porchetta + pomodori', price=5),

        Item(name='Arrosto', price=5),
        Item(name='Arrosto + patatine', price=6),
        Item(name='Arrosto + pomodori', price=6),

        Sep(name='Contorni'),
        Item(name='Patatine fritte', price=3),
        Item(name='Pomodori', price=2),

        Sep(name='Dolci'),
        Item(name='Panna cotta caramello', price=3),
        Item(name='Panna cotta cioccolato', price=3),
        Item(name='Panna cotta frutti di bosco', price=3),
        Item(name='Sorbetto limone', price=3),
        Item(name='Tartufo bianco', price=3),
        Item(name='Tartufo cioccolato', price=3),
        Item(name='Torte miste', price=3),

        Sep(name='Vino'),
        Drink(name='Sangria', price=5),
        Drink(name='Bottiglia Barbera ', price=8),
        Drink(name='Bottiglia Bonarda ', price=8),
        Drink(name='Bottiglia bianco ', price=8),
        Drink(name='Bicchiere piccolo Barbera ', price=1.5),
        Drink(name='Bicchiere piccolo Bonarda ', price=1.5),
        Drink(name='Bicchiere piccolo bianco ', price=1.5),
        Drink(name='Bicchiere grande Barbera ', price=3),
        Drink(name='Bicchiere grande Bonarda ', price=3),
        Drink(name='Bicchiere grande bianco ', price=3),

        Sep(name='Altre bevande'),
        Drink(name='Birra alla spina PILS', price=5),
        Drink(name='Birra alla spina WEISS', price=5),
        Drink(name='Bicchiere Spuma', price=0.5),
        Drink(name='Coca Cola', price=2),
        Drink(name='Aranciata', price=2),
        Drink(name='Gazzosa', price=2),
        Drink(name='The Limone', price=2),
        Drink(name='The Pesca', price=2),
        Drink(name='Acqua naturale 0.5L', price=1),
        Drink(name='Acqua frizzante 0.5L', price=1),
        Item(name='Amaro camatti', price=3),
        Item(name='Liquore liquirizia', price=3),
        Item(name='Caffe', price=1),
    ]
