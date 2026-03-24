(define (problem wipe_table)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    sponge_1 - sponge
    table_1 - surface
  )
  (:init
    (holding robot sponge_1)
    (dirty table_1)
  )
  (:goal (clean table_1))
)