import enum

    # Healthy = 0,
    # Deuteranopia = 1, # полное выпадение восприятия зеленой части спектра
    # Protanopia = 2, # полное нарушение распознавания красного спектра
    # Tritanopia = 3, # полное нарушение восприятия синего спектра
    # Achromatopsia = 4 # ч.б.


class blType(enum.Enum):
    Healthy = 0
    Deuteranopia = 1
    Protanopia = 2
    Tritanopia = 3
    Achromatopsia = 4