import json
import time
import numpy as np
from keras.preprocessing.sequence import pad_sequences

MAX_SEQUENCE_LENGTH=64
import random

class Preprocessor(object):
    def __init__(self,path):
        self.path=path
        self.n_review=0
        self.n_char=0
        self.n_word=0
        self.embedding_dim = 0
        self.max_review_words = 0
        self.max_review_chars = 0

        self.char2indice={}
        self.indice2char={}
        self.word2indice={}
        self.indice2word={}
        self.char_embedding_matrix=np.array([])

    def print_info(self):
        print('N_review:',self.n_review)
        print('N_char:',self.n_char)

    def load_char_indice(self,filename):
        self.char2indice['padding']=0
        self.indice2char[0]='padding'
        self.char2indice['unknown']=1
        self.indice2char[1]='unknown'
        self.char2indice['<sor>']=2
        self.indice2char[2]='<sor>'
        self.char2indice['<eor>']=3
        self.indice2char[3]='<eor>'
        with open(self.path+'/'+filename,encoding='utf-8') as f:
            for line in f:
                indice=len(self.char2indice)
                char=line[0]
                self.char2indice[char]=indice
                self.indice2char[indice]=char
        pass

    def load_word_indice(self,filename):
        self.word2indice['padding'] = 0
        self.indice2word[0] = 'padding'
        self.word2indice['unknown'] = 1
        self.indice2word[1] = 'unknown'
        self.word2indice['<sor>'] = 2
        self.indice2word[2] = '<sor>'
        self.word2indice['<eor>'] = 3
        self.indice2word[3] = '<eor>'

        with open(self.path+'/'+filename, encoding='utf-8') as f:
            for line in f:
                indice = len(self.word2indice)
                word = line.split('\t')[0]
                self.word2indice[word] = indice
                self.indice2word[indice] = word
        self.n_word=len(self.word2indice)
        pass

    def load_char_embedding(self,filename):
        #从filename读取一个char_embedding字典，<sor>是第0号，<eor>是第1号
        char_embedding_list=[]
        with open(self.path + '\\'  + filename,'r',encoding='utf-8',errors='ignore') as f:

            first_line=f.readline().strip().split(' ')
            self.n_char,self.embedding_dim= int(first_line[0]),int(first_line[1])

            self.char_embedding_matrix=np.empty((self.n_char,self.embedding_dim))
            #单独处理<sor> <eor>
            data = f.readline().strip().split(' ')
            cstr = r'<sor>'
            embedding_vector = tuple(map(float, data[1::]))

            indice = len(self.char2indice)
            self.char2indice[cstr] = indice
            self.indice2char[indice]=cstr
            char_embedding_list.append(embedding_vector)


            #词典里没有<eor>，先自己随机初始化一个，让它运行过程中fine tune
            cstr = r'<eor>'
            embedding_vector = tuple(map(tuple, np.random.random([1, 50])))[0]
            indice = len(self.char2indice)
            self.char2indice[cstr]=indice
            self.indice2char[indice]=cstr
            char_embedding_list.append(embedding_vector)

            for _, line in enumerate(f):

                cstr=line[0]
                data=line[1::].strip().split(' ')
                embedding_vector=tuple(map(float,data))

                indice= len(self.char2indice)
                self.char2indice[cstr]=indice
                self.indice2char[indice]=cstr

                char_embedding_list.append(embedding_vector)

        self.n_char=len(self.char2indice)
        self.char_embedding_matrix=np.array(char_embedding_list)


def sentence2vector(sentence,preprocessor):
    vector=[]
    for word in sentence:
        vector.append(preprocessor.word2indice.get(word,1))
    return vector


def vector2sentence(vector,preprocessor):
    sentence=[]
    for indice in vector:
        if indice!=0:
            sentence.append(preprocessor.indice2word[indice])
    return sentence


def read_text_json(path,word=True):
    #从json中读取评论内容和分数
    review_list=[]
    with open(path,encoding='utf-8') as json_file:
        Data=json.load(json_file)
        for shop in Data.values():
            for review in shop['reviews']:
                #score=shop[review]['comprehensive_score']
                score=review['star_rank']
                text=review['text'+'-seg'*word]
                review_list.append(tuple([text,int(score)]))
    return review_list


def read_text_tsv(path, fold, fold_i, ):
    review_list=[]

    with open(path, encoding='utf-8') as f:
        for i,line in enumerate(f):
            if i%fold == fold_i:
                try:
                    review,score = line.strip().split('\t')
                except:
                    continue
                score=int(score)

                review_list.append(tuple([review,score]))
    return review_list


def one_hot_encoder(value_vector, max_type = 5,one_index=False):
    one_hot_matrix = np.zeros([value_vector.shape[0],max_type],dtype=np.uint8)
    for i,score in enumerate(value_vector):
        one_hot_matrix[i,score-int(one_index)] = 1
    return one_hot_matrix


def build_X_Y_score(filename, preprocessor, duplicate=5, fold=10,  max_len=16,begin=-4,stop=-4):
    # 从filename中读取数据，输出三个训练数据numpy array X，Score(one_hot), Y(one_hot)

    path = preprocessor.path

    for _ in range(fold):
        review_list = read_text_tsv(path + '//' + filename, fold_i=_, fold=fold)
        X = []
        Y = []
        Score = []
        for review_score_pair in review_list:
            #对每句句子，抽 duplicate次 子串 构成训练集
            for i in range(duplicate):
                sentence_sequence=[]

                review, this_score=review_score_pair
                review=review.split(' ')
                start_index = random.choice(range(begin,len(review) + stop))
                end_index = start_index + max_len
                #end_index=random.randint(a=0,b=len(review)-1)
                #start_index=max((0,end_index-max_len))
                ii = max((0, start_index))
                jj = min(len(review), end_index)
                cut_sentence = review[ii:jj]
                if start_index < 0:
                    sentence_sequence.append(2)

                for char in cut_sentence:
                    this_indice=preprocessor.word2indice.get(char,None)
                    if this_indice:
                        sentence_sequence.append(this_indice)
                    else:
                        # 1 代表unknown
                        sentence_sequence.append(1)

                if end_index >= len(review):
                    next_char='<eor>'
                else:
                    next_char=review[jj]

                X.append(sentence_sequence)
                this_indice = preprocessor.word2indice.get(next_char,None)
                if this_indice:
                    Y.append(this_indice)
                else:
                    X.pop(-1)
                    break

                Score.append(this_score)

        X=pad_sequences(X,maxlen=max_len,dtype='int32',padding='pre',value=0)
        Y=np.array(Y)
        #print('lenY:',Y.shape)

        Score=np.array(Score)
        Score=one_hot_encoder(Score,5,one_index=True)
        yield X,Score,Y

def main():
    preprocessor=Preprocessor(r'./Data/')
    review_list=read_text_tsv('./Data/review_word.tsv',fold=100,fold_i=0)
    print(review_list[:10])

    preprocessor.load_word_indice('word_count_10.tsv')
    print(preprocessor.n_word)


    print(len(preprocessor.word2indice))
    print(len(preprocessor.indice2word))


    print(preprocessor.word2indice)
    print(preprocessor.indice2word)
    X,Score,Y=next(build_X_Y_score('review_word.tsv',preprocessor))
    print(X[:,-1],X.shape)
    print(Y.shape,Score.shape)
    pass

if __name__ == '__main__':
    main()