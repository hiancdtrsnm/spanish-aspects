
# coding: utf-8

# In[17]:


import spacy
import pydot
#from itertools import *
import es_core_news_md

from pprint import pprint
from itertools import islice
from nltk.corpus import wordnet as wn
from collections import defaultdict
#from PrintGraph import PrintGraph


# In[18]:


# WARNING!!!
# This line may take a few seconds (and a few RAM MB/GB)

nlp = es_core_news_md.load()


# In[19]:


verbs = ['dar','estudiar','durar','nacer','nace','tener','Tiene','poseer','posee','vivir','vive','trabajar','trabaja','radicar','radica','morir','muere','casar','iniciar','librar','disponer']


# In[20]:


class BuildServices:

    def __init__(self):
            pass

    def sameLevel(self,token):

        for child in token.children:
            prep = 'ADP__AdpType=Prep' in child.tag_.split('|')
            pron = 'PronType=Art' in child.tag_.replace('_','|').split('|')
            relative = 'PronType=Rel' in child.tag_.replace('_','|').split('|')
            if(prep or pron or child.pos_ == 'ADP' or child.tag_ == 'amod' or relative or child.pos_ == 'SCONJ'):
                return False

        return True


    def ChildRelative(self,token):

        for child in token.children:
            relative = 'PronType=Rel' in child.tag_.replace('_','|').split('|')
            if(relative or child.pos_ == 'SCONJ'):
                return True

        return False

    def isIn(self,aspects,token):

        for x in aspects:
            if(x.__str__() == token.__str__()):
                return True

        return False

    def buildNominal(self,token):

        aspects = [token]

        for child in token.children:

            relative = self.ChildRelative(child)

            if((child.dep_ == 'nsubj' and not relative) or child.pos_ == 'PUNCT' or child.pos_ == 'CONJ'):
                continue

            if(len(list(child.children)) > 0):
                childlist = self.buildNominal(child)

                if(self.sameLevel(child)):
                    for x in childlist:
                        aspects.append(x)

                elif(child.pos_ == 'ADJ' and token.pos_ == 'VERB'):
                    obj = self.getObj(token)
                    l = [obj,child]
                    aspects.append(l)


                else:
                    aspects = list(filter(lambda x : x.__str__() != token.__str__(), aspects))
                    for form in childlist:
                        l= [token,form]
                        aspects.append(l)


            elif(((child.pos_ == 'ADJ' and token.pos_ == 'NOUN') or child.pos_ == 'NOUN' or child.pos_ == 'ADV' or child.pos_ == 'PROPN') and not (child.pos_ == 'VERB')):
                aspects = list(filter(lambda x : x.__str__() != token.__str__(), aspects))
                l= [token,child]
                aspects.append(l)


            elif(child.pos_ == 'ADJ' or child.pos_ == 'VERB'):
                aspects.append([child])

        return aspects



    def buildSintagma(self,token):
        if(token.pos_ != 'VERB' or token.lemma_ in verbs):
            return self.buildNominal(token)

        else:
            return []


    def BuildNsubj(self,nsubj):
        s = []
        for child in nsubj.children:
            if(len(list(child.children)) == 0 or child.pos_ == 'PROPN' or not self.sameLevel(child)):
                s += self.BuildNsubj(child)

        if(nsubj.dep_ != 'nsubj'):
            s.append(nsubj)

        return s

    def BuildNsubjS(self,nsubj):
        s = ''
        for child in nsubj.children:
            if(len(list(child.children)) == 0 or child.pos_ == 'PROPN' or not self.sameLevel(child)):
                s += self.BuildNsubjS(child) + ' '

        if(nsubj.dep_ != 'nsubj'):
            s += nsubj.__str__() + ' '

        return s

    def fix(self,aspect):

        ans = []
        for elem in aspect:
            if isinstance(elem,list):
                l = self.fix(elem)
                for x in l:
                    ans.append(x)
            else:
                ans.append(elem)

        return ans

    def Rebuild(self,dic):
        for key in dic.keys():
            aspects = dic[key]
            for i in range(0,len(aspects)):
                if isinstance(aspects[i],list) and len(aspects[i]) > 1:
                    l = self.fix(aspects[i])
                    l.sort(key = lambda x : x.idx)
                    aspects[i] = l
                dic[key][i] = aspects[i]
        return dic





# In[21]:


class GetServices:

    def __init__(self):
        pass

    def getNsubj(self):
        for token in self.sent:
            if token.dep_ == 'nsubj':
                return token

    def getRoot(self):
        for token in self.sent:
            if token.dep_ == 'ROOT':
                return token

    def getObj(self,token):
        for child in token.children:
            if(child.dep_ == 'iobj' or child.dep_ == 'obj'):
                return child


    def getArticle(self,pos_fine):
        return 'Omitido'

    def getOmmited(self,token):
        if(token.pos_ != 'VERB'):
            for child in token.children:
                if(child.lemma_ == 'ser' or child.lemma_ == 'estar'):
                    return self.getArticle(child.tag_)

        return self.getArticle(token.tag_)



# In[22]:


class AspectSentence(GetServices,BuildServices):

    def __init__(self,sentence):
        self.sent = sentence

    def extractModifiers(self):
        nsub = self.getNsubj()
        l = []

        if(nsub):
            anc = list(nsub.ancestors)[0]
            while(anc.dep_ != 'ROOT'):
                l += self.buildSintagma(anc)
                anc = list(anc.ancestors)[0]

            l += self.buildSintagma(anc)

            for child in nsub.children:
                if(child.pos_ != 'DET' and (len(list(child.children)) > 0) and child.pos_ != 'PROPN' and self.sameLevel(child)):
                    l += self.buildSintagma(child)

        else:
            anc = self.getRoot()
            l = self.buildSintagma(anc)

        return {nsub.__str__() + ' ' + self.BuildNsubjS(nsub) if nsub else self.getOmmited(anc): ([[nsub] + self.BuildNsubj(nsub)] + l) if nsub else l }


    def HaveEnt(self,l):
        for token in l:
            if(token.ent_type_ and token.ent_type_ != 'NE'):
                return token

        return None




# In[23]:


def Work(sentence):

    aspect = AspectSentence(sentence)
    dic = aspect.extractModifiers()

    return dic


# In[24]:


def penn_to_wn(tag):
    if tag.startswith('N'):
        return 'n'

    if tag.startswith('V'):
        return 'v'

    if tag.startswith('J'):
        return 'a'

    if tag.startswith('R'):
        return 'r'

    return None

def transform(data):
    if not isinstance(data, list):
        data = [data]
    return {
        'tokens': data,
        'text': ' '.join([str(d) for d in sorted(data,key=lambda x:x.i)]),
        'wn': [[w for w in wn.synsets(str(d).lower(), lang='spa') if w.pos() == penn_to_wn(d.pos_) ] for d in data]
    }

def extract_aspects(text):
    doc = nlp(text)

    aspect_info = []
    last = None

    for sentence in doc.sents:
        dic = Work(sentence)
        build = BuildServices()
        dic = build.Rebuild(dic)
        aspect_info.append(dic)

    #ASPECTS:
    ans = []
    for dic in aspect_info:
        for key in dic.keys():
            for aspect in dic[key]:
                if(aspect.__str__() != 'Omitido') or str(aspect) != 'ENDOFARTICLE':
                    ans.append(aspect)

    return([transform(d) for d in ans])




# In[26]:


from sklearn.externals import joblib

reduce = joblib.load('reducelist.gz')
text = reduce[47].text
#data = [transform(d) for d in extract_aspects(text) if str(d) != 'ENDOFARTICLE']
data = extract_aspects(text)
from pprint import pprint
open('text','w').write(text)

pprint(data[:10])

