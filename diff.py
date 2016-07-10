from subprocess import Popen, PIPE, call, check_output
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
        while string[l_idx - l] != ' ':
            left -= 1
            l += 1
    else:
        left = None

    right = r_idx
    if r_idx:
        r = 0
        while string[r_idx + r] != ' ':
            right += 1
            r += 1
    else:
        right = None

    if left == None:
        l = 0
        left = r_idx-1
        while string[r_idx-1 - l] != ' ':
            l += 1
            left -= 1
    if right == None:
        r = 0
        right = l_idx+1
        while string[l_idx+1 + r] != ' ':
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

        if target0 and target1:
            idx_0 = int(target0) - 1
            idx_1 = int(target1) - 1
            keyword = kword_idx(B, idx_0, idx_1)
        elif target0:
            idx = int(target0) - 1
            keyword = kword_idx(B, l_idx=idx)
        elif target1:
            idx = int(target1) - 1
            keyword = kword_idx(B, r_idx=idx)

        l_c = 0
        for i in range(left_context):
            l_c += 1
            while B[keyword[0] - l_c] != ' ':
                l_c += 1
        r_c = 0
        for i in range(right_context):
            r_c += 1
            if keyword[1] + r_c <= len(B)-1:
                while B[keyword[1] + r_c] != ' ':
                    r_c += 1

        if source0 and source1:
            idx_0 = int(source0) - 1
            idx_1 = int(source1) - 1
            keyword_a = kword_idx(A, idx_0, idx_1)
        elif source0:
            idx = int(source0) - 1
            keyword_a = kword_idx(A, l_idx=idx)
        elif source1:
            idx = int(source1) - 1
            keyword_a = kword_idx(A, r_idx=idx)

        keyword_string_A = A[keyword_a[0]:keyword_a[1]]
        keyword_string_B = B[keyword[0]:keyword[1]]
        left_string = B[keyword[0] - l_c:keyword[0]]
        right_string = B[keyword[1]:keyword[1]+r_c]
        conc_list.append(left_string.strip()+'\t'+keyword_string_B.strip()+'('+keyword_string_A.strip()+')\t'+right_string.strip())
    return conc_list

A_path = 'gyu_cutwords_raw/'
B_path = 'gyu_manual_checked_cutwords/'

pairs = [("རྒྱུད། ཐུ།_segmented.txt", "rgyud thu_.txt"), ("རྒྱུད། པུ།_segmented.txt", "rgyud pu.txt"), ("རྒྱུད། ཏ།_segmented.txt", "rgyud ta_.txt"), ("རྒྱུད་ཡ།_segmented.txt", "rgyud ya_.txt"), ("རྒྱུད། ཞ།_segmented.txt", "rgyud zha_.txt"), ("རྒྱུད། ཀི།_segmented.txt", "rgyud ki_.txt"), ("རྒྱུད། དི།_segmented.txt", "rgyud di_.txt"), ("རྒྱུད། འ།_segmented.txt", "rgyud 'a_.txt"), ("རྒྱུད། ཝི།_segmented.txt", "rgyud wi_.txt"), ("རྒྱུད། ཁི།_segmented.txt", "rgyud khi_.txt"), ("རྒྱུད། ཛི།_segmented.txt", "rgyud dzi_.txt"), ("རྒྱུད། ཝ (1)_segmented.txt", "rgyud wa_.txt"), ("རྒྱུད། ས།_segmented.txt", "rgyud sa_.txt"), ("རྒྱུད། ཤ_segmented.txt", "rgyud sha_.txt"), ("རྒྱུད། ཇུ།_segmented.txt", "rgyud ju_.txt"), ("རྒྱུད། ཞི།_segmented.txt", "rgyud zhi_.txt"), ("རྒྱུད། རི།_segmented.txt", "rgyud ri_.txt"), ("རྒྱུད། པི།_segmented.txt", "rgyud pi_.txt"), ("རྒྱུད། ཧ།_segmented.txt", "rgyud ha_.txt"), ("རྒྱུད། ཕུ།_segmented.txt", "rgyud phu_.txt"), ("རྒྱུད། ཟི།_segmented.txt", "rgyud zi_.txt"), ("རྒྱུད། ཟ།_segmented.txt", "rgyud za_.txt"), ("རྒྱུད། ང་།_segmented.txt", "rgyud ngi_.txt"), ("རྒྱུད། ཚུ།_segmented.txt", "rgyud tshu.txt"), ("རྒྱུད། ཇ།_segmented.txt", "rgyud ja_.txt"), ("རྒྱུད། ནུ།_segmented.txt", "rgyud nu_.txt")]

total_con = defaultdict(list)
for vol in pairs:
    name = vol[0].split('_')[0]
    print(name)
    vol_diff = diff_conc(A_path+vol[0], B_path+vol[1])
    for v in vol_diff:
        total_con[name].append(v+'\t'+name)