
function check_password(pass) {
    /*
    Checks whether a password is valid or not. A password must have the following:

    1. Atleast 8 letter long
    2. Atleast 1 number
    3. Atleast 1 caps
    4. Atleast 1 special character
    */
   
    if (pass.length < 8) {
        console.log("password not longer than 8 chars");
        return false;
    }

    let i = 0;
    let caps_flag = false;
    let num_flag = false;
    let special_flag = false;

    while (i < pass.length) {
        let char = pass[i];

        if (char >= 'A' && char <= 'Z') {
            caps_flag = true;
        } else if (char >= '0' && char <= '9') {
            num_flag = true;
        } else if (!"abcdefghijklmnopqrstuvwxyz".includes(char.toLowerCase())) {
            special_flag = true;
        }

        i++;
    }

    if (!caps_flag) console.log("missing uppercase letter");
    if (!num_flag) console.log("missing number");
    if (!special_flag) console.log("missing special character");

    return caps_flag && num_flag && special_flag;
}