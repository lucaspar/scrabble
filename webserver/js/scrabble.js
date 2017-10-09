let pg = $('#game');                                                            // playground
let abc = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
           'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'];    // alphabet
let vow = ['a', 'e', 'i', 'o', 'u']                                             // vowels
let board = $("<div class='board'></div>");
let input = $("<div class='user-input row'>\
                    <input class='' type='text' name='word' autocomplete='off' placeholder='Forme uma palavra' autofocus/>\
                    <input class='btn btn-success' type='submit' name='submit' value='enviar'/>\
                </div>");
let placing;
let letterCount = 0;

function getLetter(letter) {
    if (letter.length > 1) {
        console.log('Error: Not a letter');
        return false;
    }
    return "<h2 class='letter'>"+letter+"</h2>";
}

function placeLetter(letter) {
    if (letterCount >= 20) {
        console.log('Too many letters already')
        return false;
    }
    if (!letter) {      // pick letter if undefined
        if (Math.random() >= 0.7) {      // 30% chance of picking a vowel
            letter = vow[Math.floor(Math.random() * vow.length)];
        }
        else {
            letter = abc[Math.floor(Math.random() * abc.length)];
        }
    }
    board.append(getLetter(letter));
    letterCount++;
}

function init() {
    pg.append(board);
    pg.append(input);
}

function endGame() {
    clearInterval(placing);
    let gover = 'Game Over';
    console.log(gover);
    alert(gover);
}

init();
placeLetter();
placing = setInterval(placeLetter, 1000);
//setTimeout(endGame, 900);
