#!python3
# Credit to reddit user /u/tangerinelion for their advice
import re
import database
import string


class enigma:
    """
    A simulated enigma machine that can encode and decode text
    """
    def __init__(self):
        """
        Ensures the Enigma machine has all settings
        configured for operation
        """
        self.rotor_database = database.make_db('data', 'reflectors')
        self.ab_list = list(string.ascii_uppercase)

        print('Default Configuration:\n'
              '\tModel: M3\n\tRotors (left-right): I, II, III\n'
              '\tReflector: B\n\tRing Setting: AAA\n\tGround Setting: AAZ\n'
              '\tPlugboard: None')

        setting = input('Customise configuration? (Y/N): ').lower()
        if setting.startswith('y'):
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
            model = self.rotor_database['M3']
        else:
            models = list(self.rotor_database.keys())
            print('Select model: %s' % ', '.join(models))
            model = self.rotor_database[input().title()]
        return model

    def ring_settings(self, defaults=None):
        """
        The ring setting offsets the rotor key-value pairs relative
        to the value. e.g. for Rotor M3-I:
        v: ABCDEFGHIJKLMNOPQRSTUVWXYZ,  ABCDEFGHIJKLMNOPQRSTUVWXYZ
        k: UWYGADFPVZBECKMTHXSLRINQOJ,  JUWYGADFPVZBECKMTHXSLRINQO
        """
        if defaults:
            l_ring, m_ring, r_ring = 0, 0, 0
        else:
            print('Input ring settings (A-Z):')
            l_input = input('Left: ').upper()
            l_ring = self.ab_list.index(l_input)

            m_input = input('Middle: ').upper()
            m_ring = self.ab_list.index(m_input)

            r_input = input('Right: ').upper()
            r_ring = self.ab_list.index(r_input)
        return l_ring, m_ring, r_ring

    def ground_settings(self, defaults=None):
        """
        Sets the ground setting (or starting position)
        of the rotors e.g. AAZ, BFX
        """
        if defaults:
            left, middle, right = 0, 0, 25
        else:
            print('Input start positions (A-Z):')
            left = self.ab_list.index(input('Left: ').upper())
            middle = self.ab_list.index(input('Middle: ').upper())
            right = self.ab_list.index(input('Right: ').upper())
        return [left, middle, right]

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
            rotors = ((self.rotor_database['M3']['I'],
                       self.reflected_path(self.rotor_database['M3']['I']),
                       self.rotor_database['M3']['notches']['I']),
                      (self.rotor_database['M3']['II'],
                       self.reflected_path(self.rotor_database['M3']['II']),
                       self.rotor_database['M3']['notches']['II']),
                      (self.rotor_database['M3']['III'],
                       self.reflected_path(self.rotor_database['M3']['III']),
                       self.rotor_database['M3']['notches']['III']),
                      self.rotor_database['M3']['reflectors']['B'])

        else:
            rotors = self.model
            reflectors = self.model['reflectors']

            print('Input rotor selection: '
                  '%s' % ', '.join(sorted(rotors.keys())))
            l_input = input('Left: ').upper()
            l_rotor = (rotors[l_input],)
            l_rotor += (self.reflected_path(l_rotor[0]),)

            m_input = input('Middle: ').upper()
            m_rotor = (rotors[m_input],)
            m_rotor += (self.reflected_path(m_rotor[0]),)
            m_rotor += (rotors['notches'][m_input],)

            r_input = input('Right: ').upper()
            r_rotor = (rotors[r_input],)
            r_rotor += (self.reflected_path(r_rotor[0]),)
            r_rotor += (rotors['notches'][r_input],)

            print('Select a reflector: %s' % ', '.join(reflectors))
            reflector = reflectors[input('Reflector: ').upper()]

            rotors = l_rotor, m_rotor, r_rotor, reflector

        return rotors

    def plugboard_settings(self, defaults=None):
        """
        Sets which letters are swapped on the plugboard
        """
        # Generate default plugboard where A='A', B='B', etc.
        plugboard = {ltr: ltr for ltr in self.ab_list}

        if defaults:
            return plugboard

        print('Input letter pairs for plugboard settings (A-Z).\n'
              'Leave blank for defaults or to continue.')

        used_ltrs = []
        for count in range(1, 11):
            pair = []
            for i in range(2):
                ltr = input('Enter a letter (pair %s): ' % count).upper()
                while True:
                    while ltr == '' and i == 1:
                        print("Input can't be blank.")
                        ltr = input('Enter a new letter (pair %s: '
                                    % count).upper()
                    while ltr in used_ltrs:
                        print('Letter already in use.')
                        ltr = input('Enter a new letter (pair %s): '
                                    % count).upper()
                    if ltr or i == 0:
                        break   # second input can't be blank
                if ltr == '':
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

    def rotor_encode(self, keypress):
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

        print(self.ab_list[left], self.ab_list[middle],
              self.ab_list[right])

        # Increment rotor position
        right += 1
        if right > 25:
            right = 0
        elif right == r_notch:
            middle += 1
        if middle > 25:
            middle = 0
        elif middle == (m_notch - 1) and right == (
                r_notch + 1):
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

        m_rotor_out = self.rotor_io(
            l_rotor_out, middle - left, rf_m_rotor)

        r_rotor_out = self.rotor_io(
            m_rotor_out, right - middle, rf_r_rotor)

        rotor_encode_out = self.rotor_io(r_rotor_out, -right, self.ab_list)
        return rotor_encode_out

    def ch_input(self):
        """
        Returns only valid input characters
        Valid inputs are non-accented upper-case characters A-Z
        """
        keypress = input('Enter message: ').upper()
        keypress = re.compile(r'[A-Z]').findall(keypress)
        return keypress

    def encode(self):
        """
        Runs text through the Enigma machine,
        then outputs text in groups of four characters
        """
        message = self.ch_input()
        ch_list = ''
        for ch in message:
            ch = self.plugboard_encode(ch)
            ch = self.rotor_encode(ch)
            ch = self.plugboard_encode(ch)
            ch_list += ch
        output = re.compile(r'[A-Z]{1,4}').findall(ch_list)
        output = ' '.join(output)
        return output


if __name__ == "__main__":
    machine = enigma()
    print(machine.encode())
