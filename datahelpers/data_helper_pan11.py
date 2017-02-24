import xml.etree.ElementTree as ET
import collections
import re
import numpy as np
import itertools
import pickle
from collections import Counter

# THIS FILE LOADS PAN11 DATA
# CODE 0 IS SMALL TRAINING AND TESTING, CODE 1 IS LARGE TRAINING AND TESTING


class DataHelper:
    Record = collections.namedtuple('Record', ['file', 'author', 'content'])
    Small_Author_Order = ['965226', '543719', 'x16198468117121', '997109', '464635',
                          '940826', '698837', 'x41117151611103260461997140', '636010',
                          'x159911161646101978', '580177', 'x659461599419513114', '255029',
                          '797711', 'x759461997140', 'x1297161459914695915', 'x6114104622172211485',
                          'x79721469971010', 'x64646297149114', 'x1546461997140', '900986', 'x8464695915',
                          'x12971784621399897149811', 'x10114697001411515', 'x0971411046297149114', '339173']

    Large_Author_Order = ['x9971451464197140', '904579', 'x711851046421971616', 'x1946461945161', '446543',
                          'x7599811482146199716151110', '676708', '601217', 'x99464635141110', 'x959941881469997154',
                          '280939', '995484', 'x169710974661110115', '965194', '428896', '265281', '640334', '363505',
                          '655031', 'x9710021462251212114', 'x611410469714101180', '454005', 'x8510021460111011411',
                          '894867', 'x1541881214699111499710', '664011', 'x1597882146981997',
                          'x611109716497104699979721', '273750', 'x79794671515114', 'x71185104612141151611',
                          'x811175151467516994110', '949679', '194257', 'x9464612141151611', '183141',
                          'x01716994461317538121', '761806', 'x64646719710', 'x31149780461019199', 'x95714631453159821',
                          'x1614979921463197999911101', '140914', '956947', '956112', '315875',
                          'x41180110461597851598171421', 'x997161641194681104971416', '730970',
                          'x05971097461599411816115', '100228', 'x997141651046991758897', '693864',
                          'x14110464972115811616', 'x16464681799995', 'x1519710469914971009788', 'x9746469971416510',
                          '425445', 'x151611811046719710', 'x897181114971611', 'x9111057974699971715411885',
                          'x1641199715469971416510', 'x61141046897181114971611', '339173', 'x097141411104635141110',
                          '559588', '648564', '769031', '658916', '935669', 'x10114697001411515', '580177']

    author_order = None

    training_options = ["./data/pan11-training/SmallTrain.xml", "./data/pan11-training/LargeTrain.xml"]
    testing_options = ["./data/pan11-test/SmallTest.xml", "./data/pan11-test/LargeTest.xml"]
    truth_options = ["./data/pan11-test/GroundTruthSmallTest.xml", "./data/pan11-test/GroundTruthLargeTest.xml"]

    vocabulary_size = 30000
    embedding_dim = 300

    problem_name_options = ["small", "large"]
    problem_name = None

    prob_code = None
    record_list = []
    num_of_classes = None
    train_f = None
    test_f = None
    truth_f = None

    def __init__(self, code):
        self.prob_code = code
        if code == 0:
            self.author_order = self.Small_Author_Order
        elif code == 1:
            self.author_order = self.Large_Author_Order
        else:
            print "code ERROR"
        self.train_f = self.training_options[self.prob_code]
        self.test_f = self.testing_options[self.prob_code]
        self.truth_f = self.truth_options[self.prob_code]
        self.problem_name = self.problem_name_options[self.prob_code]

    def clean_str(self, string):
        # TODO: need more thought
        string = re.sub("\"([\w])", "\" \\1", string)
        string = re.sub("([\w])\"", "\\1 \"", string)
        string = re.sub("([\w])-", "\\1 -", string)
        string = re.sub("([\w])/([\w])", "\\1 / \\2", string)

        string = re.sub("\$[\d.]+", "<<MONEY>>", string)
        string = re.sub("[\d]+/[\d]+/[\d]{4}", "<<DATE>>", string)

        string = re.sub("[-]{4,}", " <<DLINE>> ", string)
        string = re.sub("-", " - ", string)
        string = re.sub(r"[~]+", " ~ ", string)

        string = re.sub(r"\'", " \'", string)
        string = re.sub(r"</", " </", string)
        string = re.sub(r">", "> ", string)

        string = re.sub(r",", " , ", string)
        string = re.sub(r"!", " ! ", string)
        string = re.sub(r":", " : ", string)
        string = re.sub(r"\.", " . ", string)
        string = re.sub(r"\(", " ( ", string)
        string = re.sub(r"\)", " ) ", string)
        string = re.sub(r"\?", " ? ", string)
        string = re.sub(r"\s{2,}", " ", string)

        return string.strip().lower()

    def __load_train_data(self):
        data_list = []

        re_text_open = re.compile("\s*<text file=\"([\w/\.]*)\">\s*")
        re_text_clos = re.compile("\s*</text>\s*")
        re_auth = re.compile("\s*<author id=\"(\w*)\"/>\s*")
        re_body_open = re.compile("\s*<body>\s*")
        re_body_clos = re.compile("\s*</body>\s*")

        stages = ["text", "author", "body", "content", "body_clos", "text_clos"]
        expect_stage = "text"

        file_name = None
        author_name = None
        content = []

        file_content = open(self.train_f, "r").readlines()
        line_count = 0
        for l in file_content:
            line_count += 1
            l = l.strip()
            if l == "" or l == "<training>":
                pass
            elif l == "</training>":
                print "File Loading Ended: @ " + str(line_count)
                break
            elif expect_stage == "text":
                m = re_text_open.match(l)
                if m:
                    file_name = m.group(1)
                    expect_stage = "author"
                else:
                    print "ERROR"
            elif expect_stage == "author":
                m = re_auth.match(l)
                if m:
                    author_name = m.group(1)
                    expect_stage = "body"
                else:
                    print "ERROR"
            elif expect_stage == "body":
                m = re_body_open.match(l)
                if m:
                    expect_stage = "content"
                else:
                    print "ERROR"
            elif expect_stage == "content":
                m = re_body_clos.match(l)
                if m:
                    expect_stage = "text_clos"
                    r = self.Record(file=file_name, author=author_name, content=content)
                    data_list.append(r)
                    file_name = None
                    author_name = None
                    content = []
                else:
                    # l = self.clean_str(l)  # remove if no need
                    content.append(l)
            elif expect_stage == "text_clos":
                m = re_text_clos.match(l)
                if m:
                    expect_stage = "text"
                else:
                    print "ERROR"

        # for thing in data_list:
        #     print thing
        return data_list

    def __load_test_data(self):
        data_list = []

        re_text_open = re.compile("\s*<text file=\"([\w/\.]*)\">\s*")
        re_text_clos = re.compile("\s*</text>\s*")
        re_auth = re.compile("\s*<author id=\"(\w*)\"/>\s*")
        re_body_open = re.compile("\s*<body>\s*")
        re_body_clos = re.compile("\s*</body>\s*")

        stages_content = ["text", "body", "content", "body_clos", "text_clos"]
        stages_truth = ["text", "author", "text_clos"]
        expect_stage_content = "text"
        expect_stage_truth = "text"

        file_name = None
        author_name = None
        content = []

        file_content = open(self.test_f, "r").readlines()
        file_truth = open(self.truth_f, "r").readlines()

        content_line_index = 0
        truth_line_index = 0
        while content_line_index < len(file_content):
            l = file_content[content_line_index]
            content_line_index += 1
            l = l.strip()
            if l == "" or l == "<testing>":
                pass
            elif l == "</testing>":
                print "File Loading Ended: @ " + str(content_line_index)
                break
            elif expect_stage_content == "text":
                m = re_text_open.match(l)
                if m:
                    file_name = m.group(1)
                    expect_stage_content = "author"
                else:
                    print "ERROR"
            elif expect_stage_content == "author":
                content_line_index -= 1  # hold current line
                truth_loaded = False
                for truth_l in file_truth[truth_line_index:]:
                    truth_l = truth_l.strip()
                    truth_line_index += 1
                    if truth_l == "" or truth_l == "<testing>":
                        pass
                    elif expect_stage_truth == "text":
                        m = re_text_open.match(truth_l)
                        if m and m.group(1) == file_name:
                            expect_stage_truth = "author"
                        else:
                            print "ERROR: truth file mismatch"
                    elif expect_stage_truth == "author":
                        m = re_auth.match(truth_l)
                        if m:
                            author_name = m.group(1)
                            expect_stage_truth = "text_clos"
                            truth_loaded = True
                        else:
                            print "ERROR"
                    elif expect_stage_truth == "text_clos":
                        m = re_text_clos.match(truth_l)
                        if m:
                            expect_stage_truth = "text"
                            expect_stage_content = "body"
                            break
                        else:
                            print "ERROR"
                if not truth_loaded:
                    print "ERROR"
            elif expect_stage_content == "body":
                m = re_body_open.match(l)
                if m:
                    expect_stage_content = "content"
                else:
                    print "ERROR"
            elif expect_stage_content == "content":
                m = re_body_clos.match(l)
                if m:
                    expect_stage_content = "text_clos"
                    r = self.Record(file=file_name, author=author_name, content=content)
                    data_list.append(r)
                    file_name = None
                    author_name = None
                    content = []
                else:
                    # l = self.clean_str(l)  # remove if no need
                    content.append(l)
            elif expect_stage_content == "text_clos":
                m = re_text_clos.match(l)
                if m:
                    expect_stage_content = "text"
                else:
                    print "ERROR"

        # for thing in data_list:
        #     print thing
        return data_list

    def line_concat(self, data_list):
        content_len = []
        for record in data_list:
            for l in record.content:
                l += " <LB>"
            record.content = " ".join(record.content)
            # record.content = self.clean_str()
            content_len.append(len(record.content))
        print "longest content: " + str(max(content_len))
        return data_list

    def author_label(self, data_list):
        author_list = self.author_order
        author_count = {}
        for r in data_list:
            author_str = r.author
            if author_str not in author_list:
                print "WTF"
                author_list.append(author_str)  # ???
                author_count[author_str] = 1
            else:
                if author_str in author_count:
                    author_count[author_str] += 1
                else:
                    author_count[author_str] = 1

        self.num_of_classes = len(author_list)

        return author_list, author_count

    def xy_formatter(self, data_list, author_list):
        author_code = {}
        code = 0
        for key in author_list:
            author_code[key] = code
            code += 1
        x = []
        y = np.zeros((len(data_list), len(author_list)))
        global_index = 0
        for record in data_list:
            doc = " <LB> ".join(record.content)
            doc = self.clean_str(doc)
            doc = doc.split()
            x.append(doc)
            y[global_index, author_code[record.author]] = 1
            global_index += 1
        return x, y

    def build_vocab(self, reviews):
        # Build vocabulary
        word_counts = Counter(itertools.chain(*reviews))
        # Mapping from index to word
        vocabulary_inv = [x[0] for x in word_counts.most_common()]
        vocabulary_inv.insert(0, "<PAD>")
        vocabulary_inv.insert(1, "<UNK>")

        print "size of vocabulary: " + str(len(vocabulary_inv))
        # vocabulary_inv = list(sorted(vocabulary_inv))
        vocabulary_inv = list(vocabulary_inv[:self.vocabulary_size])  # limit vocab size

        # Mapping from word to index
        vocabulary = {x: i for i, x in enumerate(vocabulary_inv)}
        return [vocabulary, vocabulary_inv]

    def load_glove_vector(self):
        glove_lines = list(open("./glove.6B."+str(self.embedding_dim)+"d.txt", "r").readlines())
        glove_lines = [s.split(" ", 1) for s in glove_lines if (len(s) > 0 and s != "\n")]
        glove_words = [s[0] for s in glove_lines]
        vector_list = [s[1] for s in glove_lines]
        glove_vectors = np.array([np.fromstring(line, dtype=float, sep=' ') for line in vector_list])
        return [glove_words, glove_vectors]

    def build_embedding(self, vocabulary_inv, glove_words, glove_vectors):
        np.random.seed(10)
        embed_matrix = []
        std = np.std(glove_vectors[0, :])
        for word in vocabulary_inv:
            if word in glove_words:
                word_index = glove_words.index(word)
                embed_matrix.append(glove_vectors[word_index, :])
            else:
                embed_matrix.append(np.random.normal(loc=0.0, scale=std, size=self.embedding_dim))
        embed_matrix = np.array(embed_matrix)
        return embed_matrix

    def build_input_data(self, reviews, vocabulary):
        unk = vocabulary["<UNK>"]
        x = np.array([[vocabulary.get(word, unk) for word in rev] for rev in reviews])
        return x

    def pad_sentences(self, sentences, padding_word="<PAD>", target_length=-1):
        """
        Pads all sentences to the same length. The length is defined by the longest sentence.
        Returns padded sentences.
        """
        if target_length > 0:
            max_length = target_length
        else:
            sent_lengths = [len(x) for x in sentences]
            max_length = max(sent_lengths)
            print "longest doc: " + str(max_length)

        padded_sentences = []
        for i in range(len(sentences)):
            rev = sentences[i]
            if len(rev) <= max_length:
                num_padding = max_length - len(rev)
                new_sentence = np.concatenate([rev, np.zeros(num_padding, dtype=np.int)])
            else:
                new_sentence = rev[:max_length]
            padded_sentences.append(new_sentence)
        return np.array(padded_sentences)

    def longest_sentence(self, sentences):
        sent_lengths = [len(x) for x in sentences]
        result_index = sorted(range(len(sent_lengths)), key=lambda i: sent_lengths[i])[-10:]

        for i in result_index:
            s = sentences[i]
            print len(s)
            print s

    def load_data(self):
        # o = DataHelper(file_to_load)
        data_list = self.__load_train_data()
        author_list, author_count = self.author_label(data_list)
        print author_count
        x, y = self.xy_formatter(data_list, author_list)
        # self.longest_sentence(x)

        vocab, vocab_inv = self.build_vocab(x)
        pickle.dump([vocab, vocab_inv], open("pan11_vocabulary_"+str(self.prob_code)+".pickle", "wb"))

        [glove_words, glove_vectors] = self.load_glove_vector()
        embed_matrix = self.build_embedding(vocab_inv, glove_words, glove_vectors)

        x = self.build_input_data(x, vocab)
        x = self.pad_sentences(x, target_length=3000)
        return [x, y, vocab, vocab_inv, embed_matrix]

    def load_test_data(self):
        # o = DataHelper(file_to_load)
        data_list = self.__load_test_data()
        author_list, author_count = self.author_label(data_list)
        print author_list
        x, y = self.xy_formatter(data_list, author_list)
        self.longest_sentence(x)

        vocab, vocab_inv = pickle.load(open("pan11_vocabulary_"+str(self.prob_code)+".pickle", "rb"))

        x = self.build_input_data(x, vocab)
        x = self.pad_sentences(x, target_length=3000)
        return [x, y, vocab, vocab_inv, None]


if __name__ == "__main__":
    o = DataHelper(1)
    o.load_data()
    # o.load_test_data()
    print "o"