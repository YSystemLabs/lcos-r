(define (domain lcos-r-domestic)
  (:requirements :strips :typing)
  (:types
    object
    fridge microwave oven toaster kettle washing_machine - appliance
    towel shorts shirt - clothing
    cup bowl plate bottle pot basket drawer - container
    bed sofa wardrobe bookshelf - furniture
    table counter - surface
    vacuum broom mop cloth sponge iron hanger - tool
    container surface tool food appliance clothing document furniture location agent curtain pillow toy flower key - object
  )
  (:predicates
    (arranged ?p0 - object)
    (boiling ?p0 - container)
    (clean ?p0 - object)
    (clear ?p0 - surface)
    (closed ?p0 - container)
    (curtain_open ?p0 - object)
    (dirty ?p0 - object)
    (empty ?p0 - container)
    (folded ?p0 - clothing)
    (holding ?p0 - agent ?p1 - object)
    (hung ?p0 - clothing)
    (in ?p0 - object ?p1 - container)
    (ironed ?p0 - clothing)
    (on ?p0 - object ?p1 - surface)
    (open ?p0 - container)
    (plugged_in ?p0 - appliance)
    (powered_on ?p0 - appliance)
    (reachable ?p0 - agent ?p1 - object)
    (stacked ?p0 - object ?p1 - object)
    (fragile ?p0 - object)
    (full ?p0 - container)
    (heavy ?p0 - object)
    (hot ?p0 - object)
    (wet ?p0 - object)
    (wrinkled ?p0 - clothing)
  )
  (:action brush
    :parameters (?obj - object ?tool - tool ?agent - agent)
    :precondition (holding ?agent ?tool)
    :effect (clean ?obj)
  )
  (:action carry
    :parameters (?obj - object ?dst - location ?agent - agent)
    :precondition (holding ?agent ?obj)
    :effect ()
  )
  (:action close
    :parameters (?obj - container ?agent - agent)
    :precondition (and (reachable ?agent ?obj) (open ?obj))
    :effect (and (closed ?obj) (not (open ?obj)))
  )
  (:action drop
    :parameters (?obj - object ?agent - agent)
    :precondition (holding ?agent ?obj)
    :effect (not (holding ?agent ?obj))
  )
  (:action fold
    :parameters (?item - clothing ?agent - agent)
    :precondition (reachable ?agent ?item)
    :effect (folded ?item)
  )
  (:action grasp
    :parameters (?obj - object ?agent - agent)
    :precondition (reachable ?agent ?obj)
    :effect (holding ?agent ?obj)
  )
  (:action handover
    :parameters (?obj - object ?src - agent ?dst - agent)
    :precondition (holding ?src ?obj)
    :effect (and (holding ?dst ?obj) (not (holding ?src ?obj)))
  )
  (:action hang
    :parameters (?item - object ?hook - object ?agent - agent)
    :precondition (holding ?agent ?item)
    :effect (and (hung ?item) (not (holding ?agent ?item)))
  )
  (:action insert
    :parameters (?obj - object ?dst - object ?agent - agent)
    :precondition (holding ?agent ?obj)
    :effect (not (holding ?agent ?obj))
  )
  (:action iron
    :parameters (?item - clothing ?iron - tool ?agent - agent)
    :precondition (and (holding ?agent ?iron) (powered_on ?iron))
    :effect (and (ironed ?item) (not (wrinkled ?item)))
  )
  (:action lift
    :parameters (?obj - object ?agent - agent)
    :precondition (reachable ?agent ?obj)
    :effect (holding ?agent ?obj)
  )
  (:action mop
    :parameters (?area - surface ?mop - tool ?agent - agent)
    :precondition (holding ?agent ?mop)
    :effect (clean ?area)
  )
  (:action open
    :parameters (?obj - container ?agent - agent)
    :precondition (and (reachable ?agent ?obj) (closed ?obj))
    :effect (and (open ?obj) (not (closed ?obj)))
  )
  (:action peel
    :parameters (?food - food ?tool - tool ?agent - agent)
    :precondition (holding ?agent ?tool)
    :effect ()
  )
  (:action pick
    :parameters (?obj - object ?agent - agent)
    :precondition (and (reachable ?agent ?obj) (clear ?obj))
    :effect (and (holding ?agent ?obj) (not (on ?obj _src)))
  )
  (:action place
    :parameters (?obj - object ?dst - surface ?agent - agent)
    :precondition (holding ?agent ?obj)
    :effect (and (on ?obj ?dst) (not (holding ?agent ?obj)))
  )
  (:action pour
    :parameters (?src - container ?dst - container ?agent - agent)
    :precondition (holding ?agent ?src)
    :effect (and (empty ?src) (not (full ?dst)))
  )
  (:action press_button
    :parameters (?appliance - appliance ?agent - agent)
    :precondition (reachable ?agent ?appliance)
    :effect (powered_on ?appliance)
  )
  (:action pull
    :parameters (?obj - object ?agent - agent)
    :precondition (reachable ?agent ?obj)
    :effect ()
  )
  (:action push
    :parameters (?obj - object ?agent - agent)
    :precondition (reachable ?agent ?obj)
    :effect ()
  )
  (:action release
    :parameters (?obj - object ?agent - agent)
    :precondition (holding ?agent ?obj)
    :effect (not (holding ?agent ?obj))
  )
  (:action scoop
    :parameters (?src - container ?tool - tool ?agent - agent)
    :precondition (holding ?agent ?tool)
    :effect ()
  )
  (:action stir
    :parameters (?container - container ?tool - tool ?agent - agent)
    :precondition (holding ?agent ?tool)
    :effect ()
  )
  (:action sweep
    :parameters (?area - surface ?tool - tool ?agent - agent)
    :precondition (holding ?agent ?tool)
    :effect (clean ?area)
  )
  (:action vacuum
    :parameters (?area - surface ?vac - tool ?agent - agent)
    :precondition (and (holding ?agent ?vac) (powered_on ?vac))
    :effect (clean ?area)
  )
  (:action wipe
    :parameters (?surface - surface ?tool - tool ?agent - agent)
    :precondition (and (holding ?agent ?tool) (dirty ?surface))
    :effect (and (clean ?surface) (not (dirty ?surface)))
  )
)