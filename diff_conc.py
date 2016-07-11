from subprocess import Popen, PIPE
import tempfile
import re
from collections import defaultdict


def temp_object(content):
    temp = tempfile.NamedTemporaryFile(delete=True)
    temp.write(str.encode(content))
    return temp


def unix_diff(string_a, string_b, windows=False):
    # insert \n after every character and create a temp file
    temp_A = temp_object('\n'.join(list(string_a)) + '\n')
    temp_B = temp_object('\n'.join(list(string_b)) + '\n')
    # support for windows
    diff_command = 'diff'
    if windows:
        diff_command = 'third_parties/diff_exe/diff.exe'
    # diff call
    raw_diff = Popen([diff_command, '-H', temp_A.name, temp_B.name], shell=False, stdout=PIPE)
    return bytes.decode(raw_diff.communicate()[0])


def kword_idx(string, l_idx=0, r_idx=0):
    left = l_idx
    if l_idx:
        l = 0
        while l_idx-l <= len(string)-1 and string[l_idx - l] != ' ':
            left -= 1
            l += 1
    else:
        left = None

    right = r_idx
    if r_idx:
        r = 0
        while r_idx+r <= len(string)-1 and string[r_idx + r] != ' ':
            right += 1
            r += 1
    else:
        right = None

    if left == None:
        l = 0
        left = r_idx-1
        while r_idx-1 - l <= len(string)-1 and string[r_idx-1 - l] != ' ':
            l += 1
            left -= 1
    if right == None:
        r = 0
        right = l_idx+1
        while l_idx+1 + r <= len(string)-1 and string[l_idx+1 + r] != ' ':
            r += 1
            right += 1
    return left, right


def diff_conc(file_a, file_b, left_context=5, right_context=5):
    with open(file_a, 'r', -1, 'utf-8-sig') as f:
        A = f.read().replace('\n', '')

    with open(file_b, 'r', -1, 'utf-8-sig') as f:
        B = f.read().replace('\n', '')

    diff = unix_diff(A, B)
    diff_list = re.findall(r'\n?([^\n]+[acd][^\n]+)\n?', diff)

    conc_list = []
    for d in diff_list:
        source0, source1, target0, target1 = re.split(r'([0-9]+),?([0-9]+)?[adc]([0-9]+),?([0-9]+)?', d)[1:5]

        center = 0
        if target0 and target1:
            idx_0 = int(target0) - 1
            idx_1 = int(target1) - 1
            keyword = kword_idx(B, idx_0, idx_1)
            center = idx_0
        elif target0:
            idx = int(target0) - 1
            keyword = kword_idx(B, l_idx=idx)
            center = idx
        elif target1:
            idx = int(target1) - 1
            keyword = kword_idx(B, r_idx=idx)
            center = idx

        l_c = 0
        for i in range(left_context):
            l_c += 1
            while keyword[0] - l_c <= len(B) - 1 and B[keyword[0] - l_c] != ' ':
                l_c += 1
        r_c = 0
        for i in range(right_context):
            r_c += 1
            while keyword[1] + r_c <= len(B) - 1 and B[keyword[1] + r_c] != ' ':
                r_c += 1

        center_a = 0
        if source0 and source1:
            idx_0 = int(source0) - 1
            idx_1 = int(source1) - 1
            keyword_a = kword_idx(A, idx_0, idx_1)
            center_a = idx_0
        elif source0:
            idx = int(source0) - 1
            keyword_a = kword_idx(A, l_idx=idx)
            center_a = idx
        elif source1:
            idx = int(source1) - 1
            keyword_a = kword_idx(A, r_idx=idx)
            center_a = idx

        len_a_left = center_a - keyword_a[0]
        len_a_right = keyword_a[1] - center_a
        len_b_left = center - keyword[0]
        len_b_right = keyword[1] - center

        keyword_a_start = keyword_a[0]
        keyword_a_end = keyword_a[1]
        keyword_start = keyword[0]
        keyword_end = keyword[1]
        if len_a_left > len_b_left:
            keyword_start = center - len_a_left - 1
        if len_a_left < len_b_left:
            keyword_a_start = center_a - len_b_left - 1
        if len_a_right > len_b_right:
            keyword_end = center + len_a_right + 1
        if len_a_right < len_b_right:
            keyword_a_end = center_a + len_b_right + 1

        keyword_string_A = A[keyword_a_start:keyword_a_end].strip()
        keyword_string_B = B[keyword_start:keyword_end].strip()
        left_string = B[keyword_start - l_c:keyword_start].strip()
        right_string = B[keyword_end:keyword_end+r_c].strip()
        # debug
        #if left_string == 'ན། གནས་ ནི་ ཡིད་ མཐུན་':
        #    print(A[center_a-50:center_a+50])
        #    print(B[center-50:center+50])
        conc_list.append(left_string+'\t'+keyword_string_B+'('+keyword_string_A+')\t'+right_string)
    return conc_list


def total_diff_conc(pairs_list, a_path, b_path):
    total_conc = defaultdict(list)
    for vol in pairs_list:
        file_name = vol[0].split('_')[0]
        print(file_name)
        vol_diff = diff_conc(a_path+vol[0], b_path+vol[1])
        for v in vol_diff:
            total_conc[v.split('\t')[1]].append(v+'\t'+file_name)
    return total_conc


def write_total_diff_conc(total_conc):
    formatted_total = ''
    formatted_type_only = ''
    for token in sorted(total_conc, key=lambda x: len(total_conc[x]), reverse=True):
        title = '\t'+str(len(total_conc[token]))+' "'+token+'"\n'
        formatted_total += title
        formatted_type_only += title
        formatted_total += '\n'.join(total_conc[token])+'\n'
    return formatted_total, formatted_type_only

A_path = 'gyu_cutwords_raw/'
B_path = 'gyu_manual_checked_cutwords/'
diff_path = 'gyu_diff/'

pairs = [("རྒྱུད། ཐུ།_segmented.txt", "rgyud thu_.txt"), ("རྒྱུད། པུ།_segmented.txt", "rgyud pu.txt"), ("རྒྱུད། ཏ།_segmented.txt", "rgyud ta_.txt"), ("རྒྱུད་ཡ།_segmented.txt", "rgyud ya_.txt"), ("རྒྱུད། ཞ།_segmented.txt", "rgyud zha_.txt"), ("རྒྱུད། ཀི།_segmented.txt", "rgyud ki_.txt"), ("རྒྱུད། དི།_segmented.txt", "rgyud di_.txt"), ("རྒྱུད། འ།_segmented.txt", "rgyud 'a_.txt"), ("རྒྱུད། ཝི།_segmented.txt", "rgyud wi_.txt"), ("རྒྱུད། ཁི།_segmented.txt", "rgyud khi_.txt"), ("རྒྱུད། ཛི།_segmented.txt", "rgyud dzi_.txt"), ("རྒྱུད། ཝ (1)_segmented.txt", "rgyud wa_.txt"), ("རྒྱུད། ས།_segmented.txt", "rgyud sa_.txt"), ("རྒྱུད། ཤ_segmented.txt", "rgyud sha_.txt"), ("རྒྱུད། ཇུ།_segmented.txt", "rgyud ju_.txt"), ("རྒྱུད། ཞི།_segmented.txt", "rgyud zhi_.txt"), ("རྒྱུད། རི།_segmented.txt", "rgyud ri_.txt"), ("རྒྱུད། པི།_segmented.txt", "rgyud pi_.txt"), ("རྒྱུད། ཧ།_segmented.txt", "rgyud ha_.txt"), ("རྒྱུད། ཕུ།_segmented.txt", "rgyud phu_.txt"), ("རྒྱུད། ཟི།_segmented.txt", "rgyud zi_.txt"), ("རྒྱུད། ཟ།_segmented.txt", "rgyud za_.txt"), ("རྒྱུད། ཚུ།_segmented.txt", "rgyud tshu.txt"), ("རྒྱུད། ཇ།_segmented.txt", "rgyud ja_.txt"), ("རྒྱུད། ནུ།_segmented.txt", "rgyud nu_.txt")]

total = total_diff_conc(pairs, A_path, B_path)
output = write_total_diff_conc(total)

with open(diff_path+'total_diff.txt', 'w', -1, 'utf-8') as f:
    f.write(output[0])
with open(diff_path+'total_diff_type.txt', 'w', -1, 'utf-8') as f:
    f.write(output[1])