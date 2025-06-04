from ristomele import model

Item = model.MenuItem
Drink = lambda name, price: model.MenuItem(name=name, price=price, is_drink=True)
Foc = lambda name, price: model.MenuItem(name='Foc. '+ name, price=price)
Sep = lambda name: model.MenuItem(kind='separator', name=name)

def get_menu():
    return menu_13_agosto()
    #return menu_14_agosto()
    #return menu_sagra()

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
