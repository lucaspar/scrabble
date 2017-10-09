#!/usr/bin/python
import collections
import operator
import random
import math
import re
import os
################################################################################

# Latin alphabet (ASCII)
LETTERS = []
for k in range (0,26):
    LETTERS.append(chr(65+k))

# Letter frequencies in portuguese
FPT = [
    0.1462,  0.0104,  0.0388,  0.0499,  # a, b, c, d,
    0.1257,  0.0102,  0.013,   0.0128,  # e, f, g, h,
    0.0618,  0.004,   0.0002,  0.0278,  # i, j, k, l,
    0.0474,  0.0505,  0.1073,  0.0252,  # m, n, o, p,
    0.012,   0.0653,  0.0781,  0.0434,  # q, r, s, t,
    0.0463,  0.0167,  0.0001,  0.0021,  # u, v, w, x,
    0.0001,  0.0047                     # y, z
]

################################################################################
# Clear console screen
def clearScreen():
    os.system('clear')

################################################################################
# Return points for a given word
def calcPoints(word):

    # The final score is proportional to:
    #   the word size (base_points), and
    #   letters' rarity (multiplier)

    letters = list(word)
    points = 0
    multiplier = 1
    max_freq = max(FPT)
    base_points = len(letters)
    freq = dict(zip(LETTERS, FPT))
    for l in letters:
        # log adjusts better to the frequency curve (see Zipf's law)
        multiplier = multiplier + math.log(max_freq / float(freq[l]))

    points = int(round(base_points * multiplier))

    #print word, base_points, multiplier, points
    return points

################################################################################
# Return new board, the points, and error message (zero points if invalid play)
def process(board = [], word = None):
    error = ''
    points = 0

    if len(board) > 0 and word is not None:
        word = word.upper()
        print '\t\t\tRemoving', word, 'from', board
        if re.match('^[\w]+$', word) is None:
            error = 'Non alpha'
        else:
            bf = collections.Counter(''.join(board))
            wf = collections.Counter(word)
            for l in list(word):
                if l in bf and wf[l] <= bf[l]:
                    bf[l] = bf[l] - 1
                    wf[l] = wf[l] - 1
                    board.remove(l)
                else:
                    error = 'Letra indisponivel'
                    break

            points = calcPoints(word)

    return board, points, error

################################################################################
# Redraw game screen
def redraw(board = [], points = 0, error = ''):
    clearScreen()
    print '\n\t\t________\n\t\tSCRABBLE\n\t\tthe game\n\t\t  ----  \n\n| Tabuleiro:\t\t\t%d PTS\n|\n|' % points,
    for k,letter in enumerate(board):
        print '\t' + letter,
        if k % 4 is 3:
            print '\n|\n|',
    print '\n|\n| Forme uma palavra!',
    if (len(error) > 0):
        print '\t\tErro:', error,
    print '\n\n\t>> ',

################################################################################
# Choose a random letter given the alphabet distribution in FPT
def chooseLetter():
    arrow = 0
    rdm = random.uniform(0, 1)
    for k,l in enumerate(FPT):
        arrow = arrow + l
        if rdm <= arrow:
            return LETTERS[k]   # chosen
    print 'Random out of range. Check the code.'

#############
### TESTS ###
#############

################################################################################
# Test weighted random distribution
def testLetterDistribution(SIZE = 100000, log = False):
    dist = dict((l, 0) for l in LETTERS)
    for a in range(0,SIZE):
        dist[chooseLetter()] = dist[chooseLetter()] + 1

    idx = 0
    errors = {}
    for l,f in dist.items():
        rel_obtained = f/float(SIZE)
        rel_target = FPT[idx]
        # calculate relative error for each letter: rel_obtained - rel_target
        freq_rel_error = abs(rel_obtained-rel_target) * 100
        errors[l] = freq_rel_error
        idx = idx + 1
    sorted_errors = sorted(errors.items(), key=operator.itemgetter(1))
    sorted_errors.reverse()

    if log:
        print '\nErrors for each letter in a %dk items sample:' % (SIZE/1000)
        for k in sorted_errors:
            print '\t', k[0], ':', k[1], '\t%'
        print

    assert(len(FPT) == 26)
    assert(sum(FPT) == 1)
    assert(sorted_errors[0][1] < 15)

    print 'Passed letter distribution test'

################################################################################
# Test word scoring system
def testScoringSystem():
    assert(calcPoints('ANAGRAMA') == calcPoints('AMARGANA'))
    assert(calcPoints('GIGANTE') < calcPoints('GIGANTESCO'))
    assert(calcPoints('A') < calcPoints('Z'))

    print 'Passed scoring system test'

#############
### MAIN ###
#############

################################################################################
# Main
if __name__ == '__main__':
    print 'Running tests...'
    testLetterDistribution()
    testScoringSystem()
