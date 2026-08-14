class Concentracion_Final:
    def _init_(self, C1, C2, v1, v2):
        self.c1 = C1
        self.c2 = C2
        self.v1 = v1
        self.v2 = v2
        
    def Calculo_del_numero_total_de_Moles_de_soluto(self):
        n1 = self.c1 * self.v1
        n2 = self.c2 * self.v2