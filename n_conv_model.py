import numpy as np
import os

from keras.utils.np_utils import to_categorical
from keras.layers import Dense, Input, Dropout, merge
from keras.regularizers import l2
from keras.layers import Conv1D, MaxPooling1D, Embedding, GlobalMaxPooling1D, Flatten
from keras.callbacks import ModelCheckpoint
from keras.models import Model

from keras import backend as K

from keras_utils import load_both, load_embedding_matrix, prepare_tokenized_data, train_keras_model_cv

MAX_NB_WORDS = 16000
MAX_SEQUENCE_LENGTH = 140
VALIDATION_SPLIT = 0.1
EMBEDDING_DIM = 300

EMBEDDING_DIR = 'embedding'
EMBEDDING_TYPE = 'glove.6B.300d.txt' # 'glove.6B.%dd.txt' % (EMBEDDING_DIM)

concat_axis = 1 if K.image_dim_ordering() == 'th' else -1

texts, labels, label_map = load_both()

data, word_index = prepare_tokenized_data(texts, MAX_NB_WORDS, MAX_SEQUENCE_LENGTH)

# prepare embedding matrix
nb_words = min(MAX_NB_WORDS, len(word_index))
embedding_matrix = load_embedding_matrix(EMBEDDING_DIR + "/" + EMBEDDING_TYPE,
                                          word_index, MAX_NB_WORDS, EMBEDDING_DIM)

def gen_model():

    # load pre-trained word embeddings into an Embedding layer
    # note that we set trainable = False so as to keep the embeddings fixed
    embedding_layer = Embedding(nb_words,
                                EMBEDDING_DIM,
                                weights=[embedding_matrix],
                                input_length=MAX_SEQUENCE_LENGTH,
                                trainable=False, mask_zero=False)

    # train a 1D convnet with global maxpooling
    sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
    embedded_sequences = embedding_layer(sequence_input)

    x = Conv1D(512, 5, activation='relu', border_mode='same', init='he_uniform')(embedded_sequences)
    #x = MaxPooling1D(3)(x)

    y = Conv1D(512, 3, activation='relu', border_mode='same', init='he_uniform')(embedded_sequences)
    #y = MaxPooling1D(3)(y)

    w = Conv1D(512, 4, activation='relu', border_mode='same', init='he_uniform')(embedded_sequences)
    #w = MaxPooling1D(3)(w)

    z = Conv1D(512, 7, activation='relu', border_mode='same', init='he_uniform')(embedded_sequences)
    #z = MaxPooling1D(3)(z)

    m = merge([x, y, z, w], mode='concat', concat_axis=concat_axis)

    x = GlobalMaxPooling1D()(m)
    #x = Flatten()(m)

    x = Dense(512, activation='relu')(x)
    x = Dropout(0.5)(x)

    preds = Dense(3, activation='softmax')(x)

    model = Model(sequence_input, preds)
    return model

if __name__ == '__main__':
    train_keras_model_cv(gen_model, 'n_conv/n_conv-model', max_nb_words=MAX_NB_WORDS,
                         max_sequence_length=MAX_SEQUENCE_LENGTH, k_folds=10,
                         nb_epoch=50)

