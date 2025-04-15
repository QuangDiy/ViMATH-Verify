from math_verify import verify
from math_verify.parser import LatexExtractionConfig, StringExtractionConfig, ExprExtractionConfig, MultiChoiceExtractionConfig, parse

# Parse the gold and answer
# If you know that gold will only contain latex or expr (no latex env), use
# parse(gold, extraction_config=[LatexExtractionConfig()]) or parse(gold, extraction_config=[ExprExtractionConfig()])

gold = parse("Ta có phương trình chuyển động của vật rơi tự do với vận tốc ban đầu $v_0$ là: $s = v_0t + \frac{1}{2}gt^2$. Theo đề bài, vật rơi với vận tốc ban đầu $v_0 = 12$ m/s, gia tốc trọng trường $g = 9,8$ m/s² và thời gian rơi là $t = 7$ s. Thay các giá trị này vào phương trình, ta có: $s = (12)(7) + \frac{1}{2}(9,8)(7^2)$, $s = 84 + \frac{1}{2}(9,8)(49)$, $s = 84 + (4,9)(49)$, $s = 84 + 240,1$, $s = 324,1$ m. Vậy Bình nói đúng.", extraction_config=[MultiChoiceExtractionConfig()])
answer = parse("đúng", extraction_config=[StringExtractionConfig()])

# Order here is important!
print(verify(gold, answer))

print(gold)
print(answer)