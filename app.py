from flask import Flask, render_template, request
from pyomo.environ import *

app = Flask(__name__)

class Aula:
    def __init__(self, nombre, capacidad):
        self.nombre = nombre
        self.capacidad = capacidad

class Curso:
    def __init__(self, nombre, alumnos):
        self.nombre = nombre
        self.alumnos = alumnos

aulas_iniciales = [
    Aula("A1", 30),
    Aula("A2", 27),
    Aula("A3", 27),
    Aula("A4", 29),
    Aula("A5", 25),
    Aula("A6", 25),
    Aula("A7", 30),
    Aula("A8", 32),
    Aula("A9", 30),
    Aula("A10", 29),
    Aula("A11", 20),
    Aula("A12", 30),
    Aula("A13", 36),
    Aula("A14", 27),
    Aula("A15", 27),
    Aula("A16", 34),
    Aula("A17", 26),
    Aula("A18", 36),
    Aula("A19", 26),
    Aula("A20", 28),
    Aula("A21", 35),
    Aula("A22", 37),
    Aula("A23", 28),
    Aula("A24", 30),
    Aula("A25", 30),
    Aula("A26", 30),
    Aula("A27", 32),
    Aula("A28", 35),
    Aula("A29", 18),
    Aula("APMAR", 12)
]

aulas_especiales= []

cursos_iniciales = [
    Curso("1ESO-A", 24),
    Curso("1ESO-B", 27),
    Curso("1ESO-C", 27),
    Curso("1ESO-D", 28),
    Curso("2ESO-A", 28),
    Curso("2ESO-B", 28),
    Curso("2ESO-C", 28),
    Curso("2ESO-D", 28),
    Curso("3ESO-A", 29),
    Curso("3ESO-B", 26),
    Curso("3ESO-C", 27),
    Curso("3ESO-D", 19),
    Curso("3ESO-PMAR", 10),
    Curso("4ESO-A", 27),
    Curso("4ESO-B", 28),
    Curso("4ESO-C", 27),
    Curso("4ESO-D", 27),
    Curso("1BACH-A", 32),
    Curso("1BACH-B", 36),
    Curso("1BACH-C", 35),
    Curso("1BACH-D", 32),
    Curso("1BACH-E", 32),
    Curso("1BACH-F", 30),
    Curso("2BACH-AC", 24),
    Curso("2BACH-AH", 24),
    Curso("2BACH-B", 24),
    Curso("2BACH-C", 31),
    Curso("2BACH-D", 31),
    Curso("2BACH-I", 25)

]

aulas_fijas = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global aulas_iniciales
    aulas = []
    cursos = []
    asignaciones = []
    aulas_fijas = []

    if request.method == 'POST':
        aula_nombres = request.form.getlist('aula_nombre[]')
        aula_capacidades = [int(cap) for cap in request.form.getlist('aula_capacidad[]')]
        aula_capacidades = [cap if cap >= 0 else 0 for cap in aula_capacidades]

        curso_nombres = request.form.getlist('curso_nombre[]')
        curso_alumnos = [int(alumnos) for alumnos in request.form.getlist('curso_alumnos[]')]
        curso_alumnos = [alumnos if alumnos >= 0 else 0 for alumnos in curso_alumnos]
        
        # Recuperar las asignaciones de aulas fijas del formulario
        asignaciones_aulas = request.form.getlist('aulas_fijas[]')

        print(asignaciones_aulas)

        for aula_fija in asignaciones_aulas:
            curso_nombre, aula_nombre = aula_fija.split(" | ")
            aulas_fijas.append({"curso": curso_nombre, "aula": aula_nombre})




        model = ConcreteModel()

        model.courses = Set(initialize=curso_nombres)
        model.rooms = Set(initialize=aula_nombres)

        model.room_capacity = dict(zip(aula_nombres, aula_capacidades))
        model.course_students = dict(zip(curso_nombres, curso_alumnos))

        model.assign = Var(model.courses, model.rooms, within=Binary)


        model.assign_fijas = Param(model.courses, model.rooms, within=Binary, initialize=0, mutable=True)

        for curso_aula in aulas_fijas:
            print(curso_aula)
            curso = curso_aula["curso"]
            aula = curso_aula["aula"]
            model.assign_fijas[curso, aula] = 1  # Fijar la asignación como 1 en las aulas fijas

        def fixed_assignments_rule(model, c, r):
            return model.assign[c, r] >= model.assign_fijas[c, r]

        model.fixed_assignments_constraint = Constraint(model.courses, model.rooms, rule=fixed_assignments_rule)


        
        def objective_rule(model):
            return sum(model.assign[c, r] for c in model.courses for r in model.rooms)

        model.objective = Objective(rule=objective_rule, sense=maximize)

        def capacity_rule(model, r):
            return sum(model.course_students[c] * model.assign[c, r] for c in model.courses) <= model.room_capacity[r]

        model.capacity_constraint = Constraint(model.rooms, rule=capacity_rule)

        def one_course_per_room_rule(model, r):
            return sum(model.assign[c, r] for c in model.courses) <= 1

        model.one_course_per_room_constraint = Constraint(model.rooms, rule=one_course_per_room_rule)

        def one_room_per_course_rule(model, c):
            return sum(model.assign[c, r] for r in model.rooms) == 1

        model.one_room_per_course_constraint = Constraint(model.courses, rule=one_room_per_course_rule)

        SolverFactory('cplex_direct').solve(model)

        asignaciones = []

        for c in model.courses:
            for r in model.rooms:
                if model.assign[c, r].value == 1:
                    asignaciones.append(f"{c} --> {r} ({model.course_students[c]} / {model.room_capacity[r]}) ")

        aulas_iniciales = [Aula(nombre, capacidad) for nombre, capacidad in zip(aula_nombres, aula_capacidades)]


    return render_template('index.html', asignaciones=asignaciones, aulas=aulas_iniciales, cursos=cursos_iniciales, aulas_fijas=aulas_fijas)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
