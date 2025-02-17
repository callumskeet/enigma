#!python3
# Credit to reddit user /u/tangerinelion for their advice
import re
import database
import string


class Enigma:
    """
    A simulated enigma machine that can encode and decode text
    """

    def __init__(self):
        """
        Ensures the Enigma machine has all settings
        configured for operation
        """
        self.rotor_database = database.make_db("data", "reflectors")
        self.ab_list = list(string.ascii_uppercase)

        print(
            "Default Configuration:\n"
            "\tModel: M3\n\tRotors (left-right): I, II, III\n"
            "\tReflector: B\n\tRing Setting: AAA\n\tGround Setting: AAZ\n"
            "\tPlugboard: None"
        )

        setting = input("Customise configuration? (y/N): ").lower()
        if setting.startswith("y"):
            self.model = self.select_model()
            self.rings = self.ring_settings()
            self.ground = self.ground_settings()
            self.rotors = self.rotor_settings()
            self.plugboard = self.plugboard_settings()
        else:
            self.model = self.select_model(True)
            self.rings = self.ring_settings(True)
            self.ground = self.ground_settings(True)
            self.rotors = self.rotor_settings(True)
            self.plugboard = self.plugboard_settings(True)

    def select_model(self, defaults=None):
        if defaults:
            model = self.rotor_database["M3"]
        else:
            models = list(self.rotor_database.keys())
            while True:
                print("Select model: %s" % ", ".join(models))
                selection = input().title()
                if selection in self.rotor_database.keys():
                    model = self.rotor_database[selection]
                    return model
                print('Model "%s" not found in database.' % selection)

    def ring_settings(self, defaults=None):
        """
        The ring setting offsets the rotor key-value pairs relative
        to the value. e.g. for Rotor M3-I:
        v: ABCDEFGHIJKLMNOPQRSTUVWXYZ,  ABCDEFGHIJKLMNOPQRSTUVWXYZ
        k: UWYGADFPVZBECKMTHXSLRINQOJ,  JUWYGADFPVZBECKMTHXSLRINQO
        """
        ring_inputs = [0] * 3
        if not defaults:
            print("Input ring settings (A-Z):")
            ring_inputs = [None] * 3
            ring_names = ["Left", "Middle", "Right"]
            for i, ring in enumerate(ring_names):
                selection = ""
                while not selection.isalpha():
                    selection = input(f"{ring} : ").upper()
                ring_inputs[i] = self.ab_list.index(selection)
        return ring_inputs

    def ground_settings(self, defaults=None):
        """
        Sets the ground setting (or starting position)
        of the rotors e.g. AAZ, BFX
        """
        start_positions = [0, 0, 25]
        if not defaults:
            print("Input start positions (A-Z):")
            pos_names = ["left", "middle", "right"]
            for i, pos in enumerate(pos_names):
                selection = ""
                while not selection.isalpha():
                    selection = input(f"{pos.title()} : ").upper()
                start_positions[i] = self.ab_list.index(selection)
        return start_positions

    def reflected_path(self, rotor):
        """
        Creates a new list for the reflected signal
        """
        rotor_index = [self.ab_list.index(letter) for letter in rotor]
        rf_rotor = rotor.copy()
        for i in rotor_index:
            rf_rotor[i] = self.ab_list[rotor_index.index(i)]
        return rf_rotor

    def rotor_settings(self, defaults=None):
        """
        User selection of model, rotors and reflector
        """
        if defaults:
            rotors = (
                (
                    self.rotor_database["M3"]["I"],
                    self.reflected_path(self.rotor_database["M3"]["I"]),
                    self.rotor_database["M3"]["notches"]["I"],
                ),
                (
                    self.rotor_database["M3"]["II"],
                    self.reflected_path(self.rotor_database["M3"]["II"]),
                    self.rotor_database["M3"]["notches"]["II"],
                ),
                (
                    self.rotor_database["M3"]["III"],
                    self.reflected_path(self.rotor_database["M3"]["III"]),
                    self.rotor_database["M3"]["notches"]["III"],
                ),
                self.rotor_database["M3"]["reflectors"]["B"],
            )

        else:
            rotors = self.model
            reflectors = self.model["reflectors"]
            pos_names = ["left", "middle", "right"]
            rotor_inputs = [None] * 3
            choices = sorted(
                [k for k in rotors.keys() if k not in ["notches", "reflectors"]]
            )
            print("Input rotor selection: " "%s" % ", ".join(choices))
            for i, pos in enumerate(pos_names):
                selection = ""
                while not selection in rotors.keys():
                    selection = input(f"{pos.title()} : ").upper()
                rotor_inputs[i] = (rotors[selection],)
                rotor_inputs[i] += (self.reflected_path(rotor_inputs[i][0]),)
                if i > 0:
                    rotor_inputs[i] += (rotors["notches"][selection],)

            print("Select a reflector: %s" % ", ".join(reflectors))
            selection = ""
            while not selection in reflectors:
                selection = input("Reflector: ").upper()
            reflector = reflectors[selection]

            rotors = [*rotor_inputs, reflector]

        return rotors

    def plugboard_settings(self, defaults=None):
        """
        Sets which letters are swapped on the plugboard
        """
        # Generate default plugboard where A='A', B='B', etc.
        plugboard = {ltr: ltr for ltr in self.ab_list}

        if defaults:
            return plugboard

        print(
            "Input letter pairs for plugboard settings (A-Z).\n"
            "Leave blank for defaults or to continue."
        )

        used_ltrs = []
        for count in range(1, 11):
            pair = []
            for i in range(2):
                ltr = input("Enter a letter (pair %s): " % count).upper()
                while True:
                    while ltr == "" and i == 1:
                        print("Input can't be blank.")
                        ltr = input("Enter a new letter (pair %s: " % count).upper()
                    while ltr in used_ltrs:
                        print("Letter already in use.")
                        ltr = input("Enter a new letter (pair %s): " % count).upper()
                    if ltr or i == 0:
                        break  # second input can't be blank
                if ltr == "":
                    break
                used_ltrs += ltr
                pair += ltr
                if i == 1:  # ensures both inputs were made
                    plugboard[pair[0]] = pair[1]
                    plugboard[pair[1]] = pair[0]
            if not pair:
                break
        return plugboard

    def rotor_io(self, ch, rotation, rotor):
        """
        Determines the output of a letter run through a rotor
        """
        rotor_mapping = self.ab_list.index(ch) + rotation
        if rotor_mapping < 0 or rotor_mapping > 25:
            rotor_mapping %= 26
        return rotor[rotor_mapping]

    def plugboard_encode(self, keypress):
        """
        Runs character through the plugboard
        """
        return self.plugboard.get(keypress, keypress)

    def rotor_encode(self, keypress, show_rotors=False):
        """
        Runs text through the Enigma rotor mechanism
        """
        l_rotor, rf_l_rotor = self.rotors[0][0], self.rotors[0][1]
        m_rotor, rf_m_rotor = self.rotors[1][0], self.rotors[1][1]
        m_notch = self.rotors[1][2]
        r_rotor, rf_r_rotor = self.rotors[2][0], self.rotors[2][1]
        r_notch = self.rotors[2][2]
        reflector = self.rotors[3]

        # Start position, ground = left, middle, right
        left, middle, right = self.ground[0], self.ground[1], self.ground[2]

        if show_rotors:
            print(
                "Rotor positions:",
                self.ab_list[left],
                self.ab_list[middle],
                self.ab_list[right],
            )

        # Increment rotor position
        right += 1
        if right > 25:
            right = 0
        elif right == r_notch:
            middle += 1

        if middle > 25:
            middle = 0
        elif middle == (m_notch - 1) and right == (r_notch + 1):
            middle += 1
            left += 1

        if left > 25:
            left = 0

        self.ground = [left, middle, right]

        left -= self.rings[0]
        middle -= self.rings[1]
        right -= self.rings[2]

        for i in left, middle, right:
            i %= 26

        # Encode character
        # Subtraction accounts for the previous rotor's rotation
        # relative to the rotor being used.
        r_rotor_out = self.rotor_io(keypress, right, r_rotor)

        m_rotor_out = self.rotor_io(r_rotor_out, middle - right, m_rotor)

        l_rotor_out = self.rotor_io(m_rotor_out, left - middle, l_rotor)

        reflector_out = self.rotor_io(l_rotor_out, -left, reflector)

        l_rotor_out = self.rotor_io(reflector_out, left, rf_l_rotor)

        m_rotor_out = self.rotor_io(l_rotor_out, middle - left, rf_m_rotor)

        r_rotor_out = self.rotor_io(m_rotor_out, right - middle, rf_r_rotor)

        rotor_encode_out = self.rotor_io(r_rotor_out, -right, self.ab_list)
        return rotor_encode_out

    def input(self):
        """
        Returns only valid input characters
        Valid inputs are non-accented upper-case characters A-Z
        """
        keypress = input("Enter message: ").upper()
        keypress = re.compile(r"[A-Z]").findall(keypress)
        return keypress

    def encode(self, message):
        """
        Runs text through the Enigma machine,
        then outputs text in groups of four characters
        """
        ch_list = ""
        show_rotors = False
        for i, ch in enumerate(message):
            if i == len(message) - 1:
                show_rotors = True
            ch = self.plugboard_encode(ch)
            ch = self.rotor_encode(ch, show_rotors)
            ch = self.plugboard_encode(ch)
            ch_list += ch
        output = re.compile(r"[A-Z]{1,4}").findall(ch_list)
        output = " ".join(output)
        return output


if __name__ == "__main__":
    machine = Enigma()
    while True:
        msg = machine.input()
        msg = machine.encode(msg)
        print("Encoded message:", msg)
