
function check_password(pass) {
    /*
    Checks whether a password is valid or not. A password must have the following:

    1. Atleast 8 letter long
    2. Atleast 1 number
    3. Atleast 1 caps
    4. Atleast 1 special character

    Returns an array of error messages. Empty array means the password is valid.
    */

    let errors = [];

    if (pass.length < 8) {
        errors.push("Password must be at least 8 characters long");
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

    if (!caps_flag) errors.push("Password must contain at least 1 uppercase letter");
    if (!num_flag) errors.push("Password must contain at least 1 number");
    if (!special_flag) errors.push("Password must contain at least 1 special character");

    return errors;
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        const password = document.getElementById('passwordInput').value;
        const errorDiv = document.getElementById('passwordError');
        const errors = check_password(password);

        if (errors.length > 0) {
            e.preventDefault();
            errorDiv.innerHTML = errors.join('<br>');
            errorDiv.style.display = 'block';
        } else {
            errorDiv.style.display = 'none';
        }
    });
});