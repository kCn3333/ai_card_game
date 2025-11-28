"""Texas Hold'em Poker game controller."""

from .state import PokerState
from .rules import compare_hands
from ..cards import Deck


class PokerController:
    """Controls the flow of a Texas Hold'em game."""
    
    def __init__(self) -> None:
        self.state = PokerState()
        self.deck = Deck()
        self.new_game()
    
    def new_game(self) -> None:
        """Start a new hand."""
        self.deck = Deck()
        
        # Reset state but keep chip counts
        player_chips = self.state.player_chips
        ai_chips = self.state.ai_chips
        dealer_is_player = not self.state.dealer_is_player  # Alternate dealer
        
        self.state = PokerState(
            player_chips=player_chips,
            ai_chips=ai_chips,
            dealer_is_player=dealer_is_player,
        )
        
        # Deal hole cards
        self.state.player_hand = [self.deck.draw(), self.deck.draw()]
        self.state.ai_hand = [self.deck.draw(), self.deck.draw()]
        
        # Post blinds
        self._post_blinds()
    
    def _post_blinds(self) -> None:
        """Post small and big blinds."""
        sb = self.state.small_blind
        bb = self.state.big_blind
        
        if self.state.dealer_is_player:
            # Player is dealer/button, posts small blind
            # AI posts big blind - AI has "acted" by posting
            self.state.player_chips -= sb
            self.state.player_bet = sb
            self.state.ai_chips -= bb
            self.state.ai_bet = bb
            self.state.turn = "player"  # Small blind acts first preflop
            self.state.ai_acted = True  # Big blind counts as acted
        else:
            # AI is dealer, posts small blind
            # Player posts big blind - Player has "acted" by posting
            self.state.ai_chips -= sb
            self.state.ai_bet = sb
            self.state.player_chips -= bb
            self.state.player_bet = bb
            self.state.turn = "ai"  # Small blind acts first
            self.state.player_acted = True  # Big blind counts as acted
        
        self.state.pot = sb + bb
        self.state.current_bet = bb
    
    def player_action(self, action: str, amount: int = 0) -> str:
        """
        Handle player action.
        action: "fold", "check", "call", "raise", "all_in"
        Returns: result message
        """
        if self.state.finished or self.state.turn != "player":
            return "Not your turn"
        
        if action == "fold":
            self.state.player_folded = True
            self._finish_hand("ai")
            return "You folded"
        
        elif action == "check":
            if self.state.player_bet < self.state.current_bet:
                return "Cannot check, must call or raise"
            self.state.player_acted = True
            self._next_turn()
            return "You checked"
        
        elif action == "call":
            call_amount = self.state.current_bet - self.state.player_bet
            call_amount = min(call_amount, self.state.player_chips)
            self.state.player_chips -= call_amount
            self.state.player_bet += call_amount
            self.state.pot += call_amount
            self.state.player_acted = True
            self._next_turn()
            return f"You called ${call_amount}"
        
        elif action == "raise":
            # Minimum raise is the big blind
            min_raise = self.state.big_blind
            if amount < min_raise:
                amount = min_raise
            
            call_amount = self.state.current_bet - self.state.player_bet
            total = call_amount + amount
            total = min(total, self.state.player_chips)
            
            self.state.player_chips -= total
            self.state.player_bet += total
            self.state.pot += total
            self.state.current_bet = self.state.player_bet
            self.state.player_acted = True
            self.state.ai_acted = False  # AI needs to respond to raise
            self._next_turn()
            return f"You raised to ${self.state.current_bet}"
        
        elif action == "all_in":
            all_in_amount = self.state.player_chips
            self.state.player_chips = 0
            self.state.player_bet += all_in_amount
            self.state.pot += all_in_amount
            if self.state.player_bet > self.state.current_bet:
                self.state.current_bet = self.state.player_bet
                self.state.ai_acted = False
            self.state.player_acted = True
            self._next_turn()
            return f"You went all-in for ${all_in_amount}"
        
        return "Invalid action"
    
    def get_ai_call_amount(self) -> int:
        """Get the amount AI needs to call."""
        return self.state.current_bet - self.state.ai_bet

    def ai_action(self, decision: dict) -> tuple[str, str]:
        """
        Execute AI action based on LLM decision.
        decision: {"action": "fold|check|call|raise", "raise_amount": int, "comment": str}
        Returns: (action_name, message)
        """
        if self.state.finished or self.state.turn != "ai":
            return ("none", "")
        
        action = decision.get("action", "call")
        raise_amount = decision.get("raise_amount", 40)
        call_amount = self.state.current_bet - self.state.ai_bet
        
        if action == "fold":
            self.state.ai_folded = True
            self._finish_hand("player")
            return ("fold", "AI folds")
        
        elif action == "check":
            if call_amount > 0:
                # Can't check, must call
                action = "call"
            else:
                self.state.ai_acted = True
                self._next_turn()
                return ("check", "AI checks")
        
        if action == "call":
            call_amount = min(call_amount, self.state.ai_chips)
            if call_amount > 0:
                self.state.ai_chips -= call_amount
                self.state.ai_bet += call_amount
                self.state.pot += call_amount
            self.state.ai_acted = True
            self._next_turn()
            return ("call", f"AI calls ${call_amount}")
        
        elif action == "raise":
            # Calculate total amount needed
            total = call_amount + raise_amount
            total = min(total, self.state.ai_chips)
            
            if total <= 0:
                # Can't raise, just check/call
                self.state.ai_acted = True
                self._next_turn()
                return ("check", "AI checks")
            
            self.state.ai_chips -= total
            self.state.ai_bet += total
            self.state.pot += total
            self.state.current_bet = self.state.ai_bet
            self.state.ai_acted = True
            self.state.player_acted = False  # Player must respond
            self._next_turn()
            return ("raise", f"AI raises to ${self.state.current_bet}")
        
        return ("none", "")
    
    def _next_turn(self) -> None:
        """Advance to next turn or phase."""
        if self.state.finished:
            return
        
        # Check if betting round is complete
        if self.state.player_acted and self.state.ai_acted:
            if self.state.player_bet == self.state.ai_bet:
                self._next_phase()
                return
        
        # Switch turns
        if self.state.turn == "player":
            self.state.turn = "ai"
        else:
            self.state.turn = "player"
    
    def _next_phase(self) -> None:
        """Move to next phase of the hand."""
        # Reset betting for new round
        self.state.player_bet = 0
        self.state.ai_bet = 0
        self.state.current_bet = 0
        self.state.player_acted = False
        self.state.ai_acted = False
        
        # Dealer acts last post-flop
        if self.state.dealer_is_player:
            self.state.turn = "ai"
        else:
            self.state.turn = "player"
        
        if self.state.phase == "preflop":
            # Deal flop (3 cards)
            self.state.phase = "flop"
            self.deck.draw()  # Burn card
            self.state.community_cards.extend([
                self.deck.draw(), self.deck.draw(), self.deck.draw()
            ])
        elif self.state.phase == "flop":
            # Deal turn (1 card)
            self.state.phase = "turn"
            self.deck.draw()  # Burn card
            self.state.community_cards.append(self.deck.draw())
        elif self.state.phase == "turn":
            # Deal river (1 card)
            self.state.phase = "river"
            self.deck.draw()  # Burn card
            self.state.community_cards.append(self.deck.draw())
        elif self.state.phase == "river":
            # Showdown
            self._showdown()
    
    def _showdown(self) -> None:
        """Compare hands and determine winner."""
        self.state.phase = "showdown"
        
        winner, p_hand, a_hand = compare_hands(
            self.state.player_hand,
            self.state.ai_hand,
            self.state.community_cards
        )
        
        self.state.winning_hand = f"You: {p_hand}, AI: {a_hand}"
        self._finish_hand(winner)
    
    def _finish_hand(self, winner: str) -> None:
        """End the hand and award pot."""
        self.state.finished = True
        self.state.winner = winner
        
        if winner == "player":
            self.state.player_chips += self.state.pot
        elif winner == "ai":
            self.state.ai_chips += self.state.pot
        else:  # tie
            self.state.player_chips += self.state.pot // 2
            self.state.ai_chips += self.state.pot // 2
        
        self.state.pot = 0
    
    def can_check(self) -> bool:
        """Check if player can check."""
        return self.state.player_bet >= self.state.current_bet
    
    def call_amount(self) -> int:
        """Get amount needed to call."""
        return self.state.current_bet - self.state.player_bet
    
    def reset_chips(self) -> None:
        """Reset chips to starting amount."""
        self.state.player_chips = 1000
        self.state.ai_chips = 1000
