CodeMirror.defineSimpleMode("ludus", {
    start: [
      { regex: /\b(gameOver|comms|hp|xp|flag|build|access|immo|if|elif|else|flank|choice|backup|for|while|grind|checkpoint|resume|recall|generate)\b/, token: "keyword" },
      { regex: /\b(play|shoot|shootNxt|load|loadNum|rounds|wipe|join|drop|seek|levelUp|levelDown|toHp|toXp|toComms)\b/, token: "functions" },
      { regex: /#.*$/, token: "comment" },

      { regex: /```/, token: "comment", next: "commentBlock" },
      { regex: /"(?:[^\\]|\\.)*?"/, token: "values" },
      { regex: /\b\d+(\.\d+)?\b/, token: "values" },
      { regex: /\b(true|false|dead)\b/, token: "values" },
      { regex: /[+\-*/<>!%]=|[-+*/<>!%]|==|!=|<=|>=|:|\^|&&|\|\|/, token: "operator" },
      { regex: /\b(AND|OR)\b/, token: "operator" },
      { regex: /[{}]+/, token: "symbols" },
      { regex: /[()\[\]]+/, token: "symbols-2" },
      { regex: /[,.]+/, token: "small" },
      { regex: /\w+/, token: "variable" },
    ],
    commentBlock: [
        { regex: /[^`]+/, token: "comment" }, 
        { regex: /```/, token: "comment", next: "start" }, 
      ],
    meta: {
      lineComment: "//",
    },
  });
  