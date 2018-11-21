import xml.etree.ElementTree as ET
import logging

loger = logging.getLogger('xmls')

def itertext(text):
    head, sep, text = text.partition('</doc>')
    while sep.strip():
#         print(head, sep)
#         head = head.replace(';', '')
        head = head.replace('ENDOFARTICLE', '')
        yield head + sep
        head, sep, text = text.partition('</doc>')
#         print(text[-10:], len(text))

def iterxml(text):

    for i, text in enumerate(itertext(text)):
        try:
            yield ET.fromstring(text)

        except :
            loger.error(text)


